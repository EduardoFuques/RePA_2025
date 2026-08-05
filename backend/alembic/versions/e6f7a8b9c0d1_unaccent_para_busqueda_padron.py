"""unaccent para busqueda del padron sin acentos

Habilita la extensión `unaccent` de PostgreSQL para que la búsqueda del padrón
ignore acentos: buscar "Apostoles" debe encontrar "Apóstoles".

El endpoint la usa de forma defensiva (ver `_unaccent_disponible()` en
`src/routes/admin_registros_routes.py`): si la extensión no está, cae a un
ILIKE común. Por eso esta migración no es bloqueante.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
"""

from typing import Sequence, Union

from alembic import op

revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Requiere permisos de superusuario. En el compose el usuario es `postgres`,
    # así que corre sin problema; si fallara, la búsqueda sigue funcionando
    # (sin ignorar acentos) gracias al fallback del endpoint.
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    # No se dropea la extensión: puede estar en uso por otros objetos y su
    # ausencia no rompe nada (el endpoint tiene fallback).
    pass
