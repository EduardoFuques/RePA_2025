# services/lifecycle_service.py
"""Máquina de estados del ciclo de vida de los registros del Padrón RePA.

Centraliza las transiciones permitidas y sus efectos. Las funciones NO hacen
``commit``: el caller controla la transacción (usan ``flush`` para asignar valores).

Transiciones permitidas::

    borrador     → enviado
    enviado      → en_revision
    en_revision  → observado | rechazado | aprobado
    observado    → enviado            (el usuario corrige y reenvía)
    aprobado     → vigente | vencido
    vigente      → vencido
    vencido      → vigente            (renovación anual)
    rechazado    → (terminal)

Emisión del código RePA (decisión de negocio, ver plan de auditoría 2026-07-19):
el código se emite en el **envío** del formulario (``borrador → enviado``), NO
en la aprobación admin — el circuito de aprobación es post-lanzamiento y nadie
debe quedar bloqueado sin poder operar mientras no exista. ``aprobar()`` sigue
emitiendo el código si por algún motivo no se emitió antes (no-op en el caso
normal, ya que a esa altura ``codigo_repa`` ya está seteado).

- PF, PJ, ESA tienen código RePA propio (``emitir_codigo_repa_propio``).
- AS y AGAM no tienen identidad propia: heredan como "código de trámite" el
  código de la Persona Física que los presenta (``heredar_codigo_repa_titular``).
- Usar ``procesar_envio_si_corresponde`` desde las rutas — es idempotente y
  decide cuál de las dos formas de emisión corresponde según ``REPA_TIPO``.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models.registro_lifecycle import EstadoRegistro
from src.services.repa_code_service import PREFIJOS, generar_codigo_repa

# Vigencia anual de los formularios (el código RePA no caduca).
VIGENCIA_DIAS = 365

E = EstadoRegistro

TRANSICIONES: dict[str, set[str]] = {
    E.borrador.value: {E.enviado.value},
    E.enviado.value: {E.en_revision.value},
    E.en_revision.value: {E.observado.value, E.rechazado.value, E.aprobado.value},
    E.observado.value: {E.enviado.value},
    E.aprobado.value: {E.vigente.value, E.vencido.value},
    E.vigente.value: {E.vencido.value},
    E.vencido.value: {E.vigente.value},
    E.rechazado.value: set(),
}


class TransicionInvalida(ValueError):
    """Se intentó una transición de estado no permitida."""


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


def procesar_envio_si_corresponde(
    db: Session,
    registro,
    update_data: dict,
    *,
    get_persona_fisica_titular=None,
) -> None:
    """Envía el registro a revisión y emite su código RePA (propio o
    heredado del titular) la primera vez que el formulario se marca
    ``borrador: false``. Debe llamarse desde la ruta justo después de
    aplicar los campos del update y antes del commit.

    Args:
        registro: instancia del modelo registrable (debe tener ``REPA_TIPO``).
        update_data: dict de campos que se acaban de aplicar (con
            ``exclude_unset=True``), para detectar la transición.
        get_persona_fisica_titular: callable sin argumentos que devuelve la
            PersonaFisica del usuario, requerido solo para AS/AGAM (se llama
            de forma perezosa, no en cada request).
    """
    if not _fue_recien_enviado(registro, update_data):
        return

    enviar_a_revision(db, registro)

    if registro.REPA_TIPO in PREFIJOS:
        emitir_codigo_repa_propio(db, registro)
    elif get_persona_fisica_titular is not None:
        heredar_codigo_repa_titular(db, registro, get_persona_fisica_titular())
