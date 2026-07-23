"""add codigo_repa_titular a asociaciones y obras_audiovisuales

AS y AGAM dejan de emitir código RePA propio (repa_code_service.PREFIJOS ya
no las incluye) y en su lugar heredan como "código de trámite" el
codigo_repa de la Persona Física que los presenta. Se guarda una copia no
única (a diferencia de codigo_repa, que sí lo es) porque una misma PF puede
presentar varios registros AS/AGAM con el mismo código de trámite.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("asociaciones", sa.Column("codigo_repa_titular", sa.String(length=30), nullable=True))
    op.add_column("obras_audiovisuales", sa.Column("codigo_repa_titular", sa.String(length=30), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("obras_audiovisuales", "codigo_repa_titular")
    op.drop_column("asociaciones", "codigo_repa_titular")
