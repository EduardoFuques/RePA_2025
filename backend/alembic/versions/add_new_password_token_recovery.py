"""add new_password to token_recovery

Revision ID: add_new_password_token_recovery
Revises: add_redes_sociales_pf
Create Date: 2026-03-09

Security fix: store hashed password in DB instead of JWT payload during password recovery.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_new_password_token_recovery'
down_revision: Union[str, None] = 'add_redes_sociales_pf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('token_recovery', sa.Column('new_password', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('token_recovery', 'new_password')
