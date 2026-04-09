"""add constancia_rentas_path to personas_fisicas

Revision ID: add_constancia_rentas_pf
Revises: add_cash_rebate_extra_fields
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_constancia_rentas_pf'
down_revision: Union[str, None] = 'add_cash_rebate_extra_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('personas_fisicas', sa.Column('constancia_rentas_path', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('personas_fisicas', 'constancia_rentas_path')
