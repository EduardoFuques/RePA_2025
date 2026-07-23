"""add repa lifecycle and code

Agrega los campos de ciclo de vida y código RePA a las entidades registrables
(PF, PJ, AS, AGAM, ESA) y crea la tabla de contadores secuenciales por tipo
para la emisión del código (repa_code_counters).

Fase 1 del plan de implementación del Código RePA / ciclo de vida.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-03 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tablas de entidades registrables que reciben el ciclo de vida.
REGISTRO_TABLES = (
    "personas_fisicas",
    "personas_juridicas",
    "asociaciones",
    "obras_audiovisuales",
    "estudiantes_esa",
)


def upgrade() -> None:
    """Upgrade schema."""
    for table in REGISTRO_TABLES:
        op.add_column(table, sa.Column("codigo_repa", sa.String(length=30), nullable=True))
        op.add_column(
            table,
            sa.Column(
                "estado",
                sa.String(length=20),
                nullable=False,
                server_default="borrador",
            ),
        )
        op.add_column(table, sa.Column("fecha_envio", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("fecha_vigencia_desde", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("fecha_vigencia_hasta", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("motivo_observacion", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("motivo_rechazo", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("revisado_por", sa.String(), nullable=True))

        op.create_index(
            f"ix_{table}_codigo_repa", table, ["codigo_repa"], unique=True
        )
        op.create_foreign_key(
            f"fk_{table}_revisado_por_users",
            table,
            "users",
            ["revisado_por"],
            ["id"],
        )

    op.create_table(
        "repa_code_counters",
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("tipo"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("repa_code_counters")

    for table in REGISTRO_TABLES:
        op.drop_constraint(f"fk_{table}_revisado_por_users", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_codigo_repa", table_name=table)
        op.drop_column(table, "revisado_por")
        op.drop_column(table, "motivo_rechazo")
        op.drop_column(table, "motivo_observacion")
        op.drop_column(table, "fecha_vigencia_hasta")
        op.drop_column(table, "fecha_vigencia_desde")
        op.drop_column(table, "fecha_resolucion")
        op.drop_column(table, "fecha_revision")
        op.drop_column(table, "fecha_envio")
        op.drop_column(table, "estado")
        op.drop_column(table, "codigo_repa")
