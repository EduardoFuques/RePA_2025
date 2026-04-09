"""add distritos_rodaje, fechas_rodaje, postulante_linea_nacional, postulante_linea_misionera to tramites_fomento

Revision ID: add_cash_rebate_extra_fields
Revises: add_participante_extra_fields
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_cash_rebate_extra_fields'
down_revision: Union[str, None] = 'add_participante_extra_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tramites_fomento', sa.Column('distritos_rodaje', sa.JSON(), nullable=True))
    op.add_column('tramites_fomento', sa.Column('fechas_rodaje', sa.JSON(), nullable=True))
    op.add_column('tramites_fomento', sa.Column('postulante_linea_nacional', sa.String(255), nullable=True))
    op.add_column('tramites_fomento', sa.Column('postulante_linea_misionera', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('tramites_fomento', 'postulante_linea_misionera')
    op.drop_column('tramites_fomento', 'postulante_linea_nacional')
    op.drop_column('tramites_fomento', 'fechas_rodaje')
    op.drop_column('tramites_fomento', 'distritos_rodaje')
