"""add otros_documentos JSON column to tramites_fomento

Revision ID: add_otros_documentos_fomento
Revises: add_fomento_cash_rebate_cv
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_otros_documentos_fomento'
down_revision: Union[str, None] = 'add_fomento_cash_rebate_cv'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tramites_fomento', sa.Column('otros_documentos', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('tramites_fomento', 'otros_documentos')
