"""add redes_sociales to persona_fisica

Revision ID: add_redes_sociales_pf
Revises: bc2bcbe0847e
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_redes_sociales_pf'
down_revision: Union[str, None] = 'bc2bcbe0847e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna redes_sociales a personas_fisicas
    op.add_column('personas_fisicas', sa.Column('redes_sociales', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Eliminar columna redes_sociales de personas_fisicas
    op.drop_column('personas_fisicas', 'redes_sociales')
