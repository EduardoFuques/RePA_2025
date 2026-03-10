"""add borrador column to obras_audiovisuales

Revision ID: add_borrador_obras_audiovisuales
Revises: add_redes_sociales_pf
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_borrador_obras_audiovisuales'
down_revision: Union[str, None] = 'add_redes_sociales_pf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna borrador a obras_audiovisuales
    op.add_column('obras_audiovisuales', sa.Column('borrador', sa.Boolean(), nullable=True, server_default='true'))


def downgrade() -> None:
    # Eliminar columna borrador de obras_audiovisuales
    op.drop_column('obras_audiovisuales', 'borrador')
