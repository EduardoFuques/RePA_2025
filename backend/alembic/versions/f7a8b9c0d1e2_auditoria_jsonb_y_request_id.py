"""auditoria: details a JSONB y request_id para correlacionar con los logs

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-23

`audit_logs.details` guardaba JSON serializado dentro de una columna TEXT: se
podía leer pero no consultar, así que "mostrame todos los cambios de rol sobre
tal usuario" obligaba a traer todo y filtrar en Python. Pasa a JSONB.

Se agrega `request_id` para poder saltar de una fila de auditoría a la línea de
log canónico de la request que la generó (y viceversa).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Las filas viejas ya contienen JSON válido (audit_log siempre serializó con
    # json.dumps), pero puede haber alguna con texto suelto de antes: las que no
    # parsean se envuelven en {"raw": ...} para no perder el dato ni fallar.
    op.execute(
        """
        UPDATE audit_logs
        SET details = json_build_object('raw', details)::text
        WHERE details IS NOT NULL
          AND details <> ''
          AND left(btrim(details), 1) NOT IN ('{', '[')
        """
    )
    op.execute(
        """
        UPDATE audit_logs SET details = NULL
        WHERE details IS NOT NULL AND btrim(details) = ''
        """
    )
    op.alter_column(
        "audit_logs",
        "details",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(),
        existing_nullable=True,
        postgresql_using="details::jsonb",
    )
    # Índice GIN: habilita filtrar por contenido de `details` sin escanear todo.
    op.create_index(
        "ix_audit_logs_details_gin",
        "audit_logs",
        ["details"],
        postgresql_using="gin",
    )

    op.add_column(
        "audit_logs", sa.Column("request_id", sa.String(length=64), nullable=True)
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_column("audit_logs", "request_id")
    op.drop_index("ix_audit_logs_details_gin", table_name="audit_logs")
    op.alter_column(
        "audit_logs",
        "details",
        existing_type=postgresql.JSONB(),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="details::text",
    )
