# services/lifecycle_service.py
"""Máquina de estados del ciclo de vida de los registros del Padrón RePA.

Centraliza las transiciones permitidas y sus efectos. Las funciones NO hacen
``commit``: el caller controla la transacción (usan ``flush`` para asignar valores).

Transiciones permitidas::

    borrador     → enviado
    enviado      → en_revision
    en_revision  → observado | rechazado | aprobado
                 → enviado            (el titular corrige durante la revisión)
    observado    → enviado            (el usuario corrige y reenvía)
    aprobado     → vigente | vencido
                 → enviado            (el titular edita un registro ya aprobado)
    vigente      → vencido | enviado
    vencido      → vigente            (renovación anual)
                 → enviado            (el titular edita un registro vencido)
    rechazado    → (terminal)

Un dato publicado en el padrón no cambia sin que alguien lo apruebe: cualquier
edición del titular sobre un registro ya resuelto lo devuelve a la cola de
revisión (ver ``procesar_actualizacion``). El código RePA y las fechas de
vigencia se conservan mientras tanto, así que corregir un teléfono no da de
baja la inscripción anterior.

Emisión del código RePA (decisión de negocio, ver plan de auditoría 2026-07-19):
el código se emite en el **envío** del formulario (``borrador → enviado``), NO
en la aprobación admin — el circuito de aprobación es post-lanzamiento y nadie
debe quedar bloqueado sin poder operar mientras no exista. ``aprobar()`` sigue
emitiendo el código si por algún motivo no se emitió antes (no-op en el caso
normal, ya que a esa altura ``codigo_repa`` ya está seteado).

- PF, PJ, ESA tienen código RePA propio (``emitir_codigo_repa_propio``).
- AS y AGAM no tienen identidad propia: heredan como "código de trámite" el
  código de la Persona Física que los presenta (``heredar_codigo_repa_titular``).
- Usar ``procesar_actualizacion`` desde las rutas — es idempotente y
  decide cuál de las dos formas de emisión corresponde según ``REPA_TIPO``.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.models.registro_lifecycle import EstadoRegistro
from src.services.repa_code_service import PREFIJOS, generar_codigo_repa

# Vigencia anual de los formularios (el código RePA no caduca).
VIGENCIA_DIAS = 365

E = EstadoRegistro

TRANSICIONES: dict[str, set[str]] = {
    E.borrador.value: {E.enviado.value},
    E.enviado.value: {E.en_revision.value},
    E.en_revision.value: {
        E.observado.value,
        E.rechazado.value,
        E.aprobado.value,
        # El titular corrigió datos mientras el registro estaba en revisión: el
        # revisor tiene que volver a mirarlo sobre los datos nuevos.
        E.enviado.value,
    },
    E.observado.value: {E.enviado.value},
    # Un registro ya resuelto que el titular vuelve a editar regresa a la cola
    # de revisión: un cambio de apellido o de domicilio no puede quedar
    # publicado en el padrón sin que alguien lo apruebe.
    E.aprobado.value: {E.vigente.value, E.vencido.value, E.enviado.value},
    E.vigente.value: {E.vencido.value, E.enviado.value},
    E.vencido.value: {E.vigente.value, E.enviado.value},
    E.rechazado.value: set(),
}

# Estados en los que una edición del titular obliga a revalidar. Se excluye
# `rechazado` a propósito: es terminal, y `borrador`/`observado`/`enviado`
# porque todavía no hay nada aprobado que proteger.
ESTADOS_QUE_REQUIEREN_REVALIDACION = frozenset(
    {
        E.en_revision.value,
        E.aprobado.value,
        E.vigente.value,
        E.vencido.value,
    }
)


class TransicionInvalida(ValueError):
    """Se intentó una transición de estado no permitida."""


class EdicionNoPermitida(ValueError):
    """El titular intentó una edición que el estado del registro no admite."""


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def puede_transicionar(actual: str, nuevo: str) -> bool:
    """Indica si la transición ``actual → nuevo`` está permitida."""
    return nuevo in TRANSICIONES.get(actual, set())


def _transicionar(registro, nuevo: str) -> None:
    actual = registro.estado
    if not puede_transicionar(actual, nuevo):
        raise TransicionInvalida(f"Transición no permitida: {actual!r} → {nuevo!r}")
    registro.estado = nuevo


def enviar_a_revision(db: Session, registro) -> None:
    """El usuario envía su registro (borrador/observado → enviado)."""
    _transicionar(registro, E.enviado.value)
    registro.fecha_envio = _ahora()
    db.flush()


def tomar_para_revision(db: Session, registro) -> None:
    """Un revisor toma el registro para evaluarlo (enviado → en_revision)."""
    _transicionar(registro, E.en_revision.value)
    registro.fecha_revision = _ahora()
    db.flush()


def aprobar(db: Session, registro, revisor_id: str | None = None) -> str:
    """Aprueba el registro: emite el código RePA (si no tiene), fija vigencia y revisor.

    Devuelve el código RePA asignado. El código es inmutable: si ya existía se conserva.
    """
    _transicionar(registro, E.aprobado.value)
    ahora = _ahora()
    registro.fecha_resolucion = ahora
    registro.revisado_por = revisor_id
    registro.fecha_vigencia_desde = ahora
    registro.fecha_vigencia_hasta = ahora + timedelta(days=VIGENCIA_DIAS)
    if not registro.codigo_repa:
        registro.codigo_repa = generar_codigo_repa(db, registro.REPA_TIPO)
    db.flush()
    return registro.codigo_repa


def observar(db: Session, registro, motivo: str, revisor_id: str | None = None) -> None:
    """El revisor observa el registro y lo devuelve al usuario (en_revision → observado)."""
    _transicionar(registro, E.observado.value)
    registro.motivo_observacion = motivo
    registro.fecha_resolucion = _ahora()
    registro.revisado_por = revisor_id
    db.flush()


def rechazar(db: Session, registro, motivo: str, revisor_id: str | None = None) -> None:
    """El revisor rechaza el registro (en_revision → rechazado, terminal)."""
    _transicionar(registro, E.rechazado.value)
    registro.motivo_rechazo = motivo
    registro.fecha_resolucion = _ahora()
    registro.revisado_por = revisor_id
    db.flush()


def marcar_vencido(db: Session, registro) -> None:
    """Marca el registro como vencido por caducidad anual (aprobado/vigente → vencido)."""
    _transicionar(registro, E.vencido.value)
    db.flush()


def renovar(db: Session, registro) -> None:
    """Renueva la vigencia anual de un registro vencido (vencido → vigente)."""
    _transicionar(registro, E.vigente.value)
    ahora = _ahora()
    registro.fecha_vigencia_desde = ahora
    registro.fecha_vigencia_hasta = ahora + timedelta(days=VIGENCIA_DIAS)
    db.flush()


# --------------------------------------------------------------------------- #
# Emisión de código RePA en el envío (no en la aprobación, ver docstring)     #
# --------------------------------------------------------------------------- #


def emitir_codigo_repa_propio(db: Session, registro) -> str:
    """PF/PJ/ESA: asigna código propio la primera vez que se envía el formulario.

    Idempotente — si el registro ya tiene código (p. ej. reenvío tras
    observación), no lo regenera: el código es inmutable una vez emitido.
    """
    if not registro.codigo_repa:
        registro.codigo_repa = generar_codigo_repa(db, registro.REPA_TIPO)
    db.flush()
    return registro.codigo_repa


def heredar_codigo_repa_titular(db: Session, registro, persona_fisica) -> str | None:
    """AS/AGAM: no tienen código propio — heredan el de la Persona Física
    titular como "código de trámite" (``codigo_repa_titular``, un campo
    aparte del ``codigo_repa`` del mixin, que para estos dos tipos queda
    siempre NULL).

    Si la persona física todavía no tiene su propio código emitido (no
    debería pasar en el flujo normal, ya que PF es el primer formulario
    obligatorio) no rompe: deja el campo como estaba y el caller puede
    reintentar en un envío posterior.
    """
    if persona_fisica and persona_fisica.codigo_repa:
        registro.codigo_repa_titular = persona_fisica.codigo_repa
    db.flush()
    return registro.codigo_repa_titular


def _fue_recien_enviado(registro, update_data: dict) -> bool:
    """Detecta si esta actualización es el primer envío del formulario:
    ``borrador`` pasa a ``False`` explícitamente y el registro todavía
    estaba en estado ``borrador``. Idempotente: en ediciones posteriores
    (el estado ya no es ``borrador``) devuelve False sin volver a emitir
    código ni reenviar."""
    return update_data.get("borrador") is False and registro.estado == E.borrador.value


# Campos que no cuentan como "cambio de datos" para decidir si hay que
# revalidar: el propio flag de envío y todo lo que escribe el ciclo de vida.
_CAMPOS_NO_SUSTANTIVOS = frozenset(
    {
        "borrador",
        "estado",
        "codigo_repa",
        "codigo_repa_titular",
        "fecha_envio",
        "fecha_revision",
        "fecha_resolucion",
        "fecha_ultima_actualizacion",
        "fecha_vigencia_desde",
        "fecha_vigencia_hasta",
        "motivo_observacion",
        "motivo_rechazo",
        "revisado_por",
    }
)


def campos_realmente_modificados(registro, update_data: dict) -> list[str]:
    """Campos de datos cuyo valor cambió de verdad en esta actualización.

    Compara contra el valor que tenía el objeto antes del ``setattr``, usando el
    historial de SQLAlchemy — no alcanza con mirar qué claves trae el payload.
    Los formularios autoguardan: cada pocos segundos mandan el mismo contenido,
    y tomar "vino en el payload" como "cambió" haría que un registro aprobado
    volviera a la cola de revisión solo por tenerlo abierto en pantalla.
    """
    estado_orm = inspect(registro)
    modificados = []
    for campo in update_data:
        if campo in _CAMPOS_NO_SUSTANTIVOS:
            continue
        try:
            historial = estado_orm.attrs[campo].history
        except KeyError:
            continue
        if historial.has_changes():
            modificados.append(campo)
    return modificados


def _sincronizar_borrador(registro) -> None:
    """Mantiene el booleano ``borrador`` alineado con ``estado``.

    Los dos conviven porque el frontend envía el formulario poniendo
    ``borrador: false`` y el buscador del padrón filtra por ese campo. Que sean
    dos fuentes de verdad separadas es lo que permitía desincronizarlas: un
    registro podía quedar ``estado=aprobado`` con ``borrador=True`` y
    desaparecer del buscador sin dejar de figurar como aprobado. Acá el estado
    manda y el booleano lo sigue.
    """
    if hasattr(registro, "borrador"):
        registro.borrador = registro.estado == E.borrador.value


def procesar_actualizacion(
    db: Session,
    registro,
    update_data: dict,
    *,
    get_persona_fisica_titular=None,
) -> None:
    """Punto único por el que pasa toda edición del titular sobre su registro.

    Debe llamarse desde la ruta justo después de aplicar los campos del update
    y antes del commit. Resuelve cuatro cosas:

    1. **Primer envío.** Cuando el formulario se marca ``borrador: false``
       estando en ``borrador``, el registro pasa a ``enviado`` y se emite su
       código RePA (propio para PF/PJ/ESA, heredado del titular para AS/AGAM).

    2. **Edición de un registro ya resuelto.** Si el titular cambia datos
       cuando el registro está aprobado, vigente, vencido o en revisión, vuelve
       a la cola de revisión: un cambio de apellido o de domicilio no puede
       quedar publicado en el padrón sin que un revisor lo apruebe. El código
       RePA se conserva (es inmutable) y las fechas de vigencia también, así
       que la inscripción anterior sigue valiendo mientras la corrección
       espera resolución — corregir un teléfono no da de baja a nadie.

    3. **Sello de actualización.** Cualquier cambio real de datos actualiza
       ``fecha_ultima_actualizacion``, que es lo que responde "¿cuán al día
       está lo que figura en el padrón?".

    4. **Sincronía del booleano ``borrador``** con ``estado``, para que no
       puedan volver a contradecirse.

    Args:
        registro: instancia del modelo registrable (debe tener ``REPA_TIPO``).
        update_data: dict de campos que se acaban de aplicar (con
            ``exclude_unset=True``).
        get_persona_fisica_titular: callable sin argumentos que devuelve la
            PersonaFisica del usuario, requerido solo para AS/AGAM (se llama
            de forma perezosa, no en cada request).
    """
    modificados = campos_realmente_modificados(registro, update_data)

    # Un registro que ya salió de borrador no puede volver a marcarse como
    # borrador: era la vía por la que estado y booleano quedaban en desacuerdo.
    if update_data.get("borrador") is True and registro.estado != E.borrador.value:
        raise EdicionNoPermitida(
            "El registro ya fue enviado y no puede volver al estado de "
            "borrador. Para corregirlo, editá los datos y se reenviará a "
            "revisión automáticamente."
        )

    if _fue_recien_enviado(registro, update_data):
        enviar_a_revision(db, registro)
        if registro.REPA_TIPO in PREFIJOS:
            emitir_codigo_repa_propio(db, registro)
        elif get_persona_fisica_titular is not None:
            heredar_codigo_repa_titular(db, registro, get_persona_fisica_titular())

    elif modificados and registro.estado in ESTADOS_QUE_REQUIEREN_REVALIDACION:
        _reenviar_para_revalidacion(db, registro)

    if modificados:
        registro.fecha_ultima_actualizacion = _ahora()

    _sincronizar_borrador(registro)
    db.flush()


def _reenviar_para_revalidacion(db: Session, registro) -> None:
    """Devuelve a la cola de revisión un registro ya resuelto que fue editado.

    Se limpian los motivos de la revisión anterior —hablaban de una versión de
    los datos que ya no existe— y se sella ``fecha_envio`` de nuevo. NO se toca
    ``codigo_repa`` (inmutable) ni la vigencia: la inscripción previa sigue en
    pie hasta que la corrección se resuelva.
    """
    _transicionar(registro, E.enviado.value)
    registro.fecha_envio = _ahora()
    registro.fecha_revision = None
    registro.fecha_resolucion = None
    registro.motivo_observacion = None
    registro.motivo_rechazo = None
    registro.revisado_por = None
    db.flush()
