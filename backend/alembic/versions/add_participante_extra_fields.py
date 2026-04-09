"""add formacion_previa, proyectos_en_desarrollo, participacion_capacitaciones_iaavim to participantes_semillero

Revision ID: add_participante_extra_fields
Revises: add_semillero_fomento
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_participante_extra_fields'
down_revision: Union[str, None] = 'add_semillero_fomento'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('participantes_semillero', sa.Column('formacion_previa', sa.Text(), nullable=True))
    op.add_column('participantes_semillero', sa.Column('proyectos_en_desarrollo', sa.Text(), nullable=True))
    op.add_column('participantes_semillero', sa.Column('participacion_capacitaciones_iaavim', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('participantes_semillero', 'participacion_capacitaciones_iaavim')
    op.drop_column('participantes_semillero', 'proyectos_en_desarrollo')
    op.drop_column('participantes_semillero', 'formacion_previa')
