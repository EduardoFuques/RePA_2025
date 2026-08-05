"""Búsqueda de texto insensible a acentos.

Quien busca en el padrón escribe "Apostoles", no "Apóstoles", y un `ILIKE`
común no encuentra nada. Postgres resuelve esto con la extensión `unaccent`
(migración `e6f7a8b9c0d1`).

Si la extensión no está —migración sin correr, o un motor que no es Postgres en
los tests— la búsqueda cae a un `ILIKE` común: sigue funcionando, solo que
distingue acentos. Preferimos degradar antes que romper la pantalla.
"""

import logging

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# La capacidad no cambia durante la vida del proceso: se chequea una sola vez.
_unaccent_cache: bool | None = None


def unaccent_disponible(db: Session) -> bool:
    """¿Está disponible la extensión `unaccent`?"""
    global _unaccent_cache
    if _unaccent_cache is None:
        try:
            db.execute(text("SELECT unaccent('á')"))
            _unaccent_cache = True
        except Exception:
            db.rollback()
            _unaccent_cache = False
            logger.warning(
                "Extensión 'unaccent' no disponible: las búsquedas distinguirán "
                "acentos. Correr la migración e6f7a8b9c0d1."
            )
    return _unaccent_cache


def filtro_texto(db: Session, campos, termino: str):
    """OR de coincidencias parciales sobre `campos`, ignorando acentos si se puede."""
    if unaccent_disponible(db):
        patron = f"%{termino}%"
        return or_(
            *[func.unaccent(campo).ilike(func.unaccent(patron)) for campo in campos]
        )
    return or_(*[campo.ilike(f"%{termino}%") for campo in campos])
