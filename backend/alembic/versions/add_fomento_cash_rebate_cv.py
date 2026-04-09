"""add cash rebate fields to tramites_fomento and cv_path to evaluadores

Revision ID: add_fomento_cash_rebate_cv
Revises: add_borrador_obras_audiovisuales
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_fomento_cash_rebate_cv'
down_revision: Union[str, None] = 'add_borrador_obras_audiovisuales'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cash Rebate fields on tramites_fomento
    op.add_column('tramites_fomento', sa.Column('monto_estimado_reintegro', sa.Integer(), nullable=True))
    op.add_column('tramites_fomento', sa.Column('gastos_elegibles', sa.Text(), nullable=True))
    op.add_column('tramites_fomento', sa.Column('montos_invertidos_provincia', sa.Integer(), nullable=True))

    # CV path on evaluadores
    op.add_column('evaluadores', sa.Column('cv_path', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('evaluadores', 'cv_path')
    op.drop_column('tramites_fomento', 'montos_invertidos_provincia')
    op.drop_column('tramites_fomento', 'gastos_elegibles')
    op.drop_column('tramites_fomento', 'monto_estimado_reintegro')
