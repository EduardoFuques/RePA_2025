"""add localidad y distrito a exhibiciones

El formulario de Exhibiciones ya pedía localidad y distrito audiovisual,
pero el modelo Exhibicion no tenía columnas para persistirlos (a diferencia
de Sala y Festival, que sí las tienen) - los datos se perdían al guardar.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("exhibiciones", sa.Column("localidad", sa.String(length=100), nullable=True))
    op.add_column("exhibiciones", sa.Column("distrito", sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("exhibiciones", "distrito")
    op.drop_column("exhibiciones", "localidad")
