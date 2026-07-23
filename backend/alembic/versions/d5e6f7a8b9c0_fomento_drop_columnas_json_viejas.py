"""Fomento: dropear columnas JSON viejas (pagos, otros_aportes_no_iaavim, integrantes)

Segunda de dos migraciones (ver c4d5e6f7a8b9, que creó las tablas
relacionales y copió los datos). Esta recién ahora dropea las columnas JSON
originales, una vez que el backfill de la migración anterior ya se
verificó. El downgrade recrea las columnas vacías (no reconstruye el JSON
desde las tablas relacionales — si hace falta volver atrás de verdad, los
datos siguen intactos en `pagos_fomento`/`aportes_fomento`/
`integrantes_comite`, que esta migración no toca).

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-21 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("tramites_fomento", "pagos")
    op.drop_column("tramites_fomento", "otros_aportes_no_iaavim")
    op.drop_column("comites_fomento", "integrantes")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("tramites_fomento", sa.Column("pagos", sa.JSON(), nullable=True))
    op.add_column(
        "tramites_fomento",
        sa.Column("otros_aportes_no_iaavim", sa.JSON(), nullable=True),
    )
    op.add_column("comites_fomento", sa.Column("integrantes", sa.JSON(), nullable=True))
