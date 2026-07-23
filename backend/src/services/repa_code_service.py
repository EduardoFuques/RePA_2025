# services/repa_code_service.py
"""Generación del código RePA por tipo de entidad.

El código se emite **una sola vez**, al enviar el registro (no al aprobarlo —
ver `lifecycle_service`), y es inmutable. La generación es atómica y
secuencial por tipo usando la tabla ``repa_code_counters`` con bloqueo de fila
(``SELECT ... FOR UPDATE``) para evitar duplicados bajo concurrencia.

Formato (default, encapsulado aquí para poder ajustarlo según defina el PM):
    ``{PREFIJO}{secuencia:0{ancho}d}``  →  p. ej. ``PF000001``, ``PJ000042``.

Sub-pregunta abierta (§0 del plan): ancho de secuencia, inclusión de año y prefijo por tipo
vs correlativo único. Cambiar sólo las constantes / ``build_codigo`` impacta todo el sistema.
"""

from sqlalchemy.orm import Session

from src.models.registro_lifecycle import RepaCodeCounter

# Prefijo por tipo de entidad registrable con código RePA PROPIO.
#
# AS (Asociación) y AGAM (obra audiovisual) NO están acá a propósito: no
# generan código propio, usan como "código de trámite" el codigo_repa de la
# Persona Física que los presenta (ver lifecycle_service.heredar_codigo_repa_titular).
PREFIJOS = {
    "PF": "PF",
    "PJ": "PJ",
    "ESA": "ESA",
}

# Ancho de la secuencia numérica (default reversible).
ANCHO_SECUENCIA = 6


class TipoEntidadInvalido(ValueError):
    """El tipo de entidad no tiene prefijo de código RePA definido."""


def build_codigo(tipo: str, secuencia: int) -> str:
    """Construye el string del código a partir del tipo y el número de secuencia."""
    if tipo not in PREFIJOS:
        raise TipoEntidadInvalido(f"Tipo de entidad sin prefijo RePA: {tipo!r}")
    return f"{PREFIJOS[tipo]}{secuencia:0{ANCHO_SECUENCIA}d}"


def _next_secuencia(db: Session, tipo: str) -> int:
    """Incrementa y devuelve el siguiente número de secuencia para el tipo, con bloqueo."""
    counter = (
        db.query(RepaCodeCounter)
        .filter(RepaCodeCounter.tipo == tipo)
        .with_for_update()
        .first()
    )
    if counter is None:
        # Primera emisión para este tipo: crear contador en 0 y volver a tomarlo con lock.
        db.add(RepaCodeCounter(tipo=tipo, last_value=0))
        db.flush()
        counter = (
            db.query(RepaCodeCounter)
            .filter(RepaCodeCounter.tipo == tipo)
            .with_for_update()
            .first()
        )
    counter.last_value += 1
    db.flush()
    return counter.last_value


def generar_codigo_repa(db: Session, tipo: str) -> str:
    """Genera y reserva el siguiente código RePA para el tipo de entidad indicado.

    Debe llamarse dentro de la transacción de aprobación del registro. No hace ``commit``;
    el caller controla la transacción.
    """
    if tipo not in PREFIJOS:
        raise TipoEntidadInvalido(f"Tipo de entidad sin prefijo RePA: {tipo!r}")
    secuencia = _next_secuencia(db, tipo)
    return build_codigo(tipo, secuencia)
