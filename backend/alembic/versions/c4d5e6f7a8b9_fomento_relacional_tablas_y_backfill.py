"""Fomento: tablas relacionales para pagos/aportes/integrantes (aditiva)

Primera de dos migraciones (ver también d5e6f7a8b9c0, que dropea las
columnas JSON viejas). Esta es puramente aditiva: crea `pagos_fomento`,
`aportes_fomento`, `integrantes_comite` y copia ahí el contenido actual de
`tramites_fomento.pagos`, `tramites_fomento.otros_aportes_no_iaavim` y
`comites_fomento.integrantes` (JSON). Las columnas JSON viejas NO se tocan
todavía — quedan como respaldo hasta confirmar en un ambiente real que el
backfill se ve bien, y recién ahí se dropean en la siguiente migración.

Dividir en dos migraciones (en vez de crear+backfillear+dropear en una
sola) separa el paso "aditivo y repetible sin drama" del paso "requiere
confianza total" — si algo del backfill se ve raro, alcanza con no correr
la segunda migración todavía, sin haber perdido las columnas originales.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pagos_fomento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tramite_id", sa.Integer(),
            sa.ForeignKey("tramites_fomento.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fecha", sa.DateTime(), nullable=True),
        sa.Column("monto", sa.Integer(), nullable=True),
        sa.Column("moneda", sa.String(10), nullable=True),
        sa.Column("concepto", sa.String(255), nullable=True),
        sa.Column("comprobante", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_pagos_fomento_tramite_id", "pagos_fomento", ["tramite_id"]
    )

    op.create_table(
        "aportes_fomento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tramite_id", sa.Integer(),
            sa.ForeignKey("tramites_fomento.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organismo", sa.String(255), nullable=True),
        sa.Column("programa", sa.String(255), nullable=True),
        sa.Column("monto", sa.Integer(), nullable=True),
        sa.Column("moneda", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_aportes_fomento_tramite_id", "aportes_fomento", ["tramite_id"]
    )

    op.create_table(
        "integrantes_comite",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "comite_id", sa.Integer(),
            sa.ForeignKey("comites_fomento.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Sin ondelete: preserva integridad histórica (ver modelo).
        sa.Column(
            "evaluador_id", sa.Integer(),
            sa.ForeignKey("evaluadores.id"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_integrantes_comite_comite_id", "integrantes_comite", ["comite_id"]
    )
    op.create_index(
        "ix_integrantes_comite_evaluador_id", "integrantes_comite", ["evaluador_id"]
    )

    # --- Backfill desde las columnas JSON existentes ---
    conn = op.get_bind()

    tramites = conn.execute(
        sa.text(
            "SELECT id, pagos, otros_aportes_no_iaavim FROM tramites_fomento "
            "WHERE pagos IS NOT NULL OR otros_aportes_no_iaavim IS NOT NULL"
        )
    ).fetchall()
    for row in tramites:
        for pago in (row.pagos or []):
            if not isinstance(pago, dict):
                continue
            conn.execute(
                sa.text(
                    "INSERT INTO pagos_fomento "
                    "(tramite_id, fecha, monto, moneda, concepto, comprobante, created_at) "
                    "VALUES (:tramite_id, :fecha, :monto, :moneda, :concepto, :comprobante, now())"
                ),
                {
                    "tramite_id": row.id,
                    "fecha": pago.get("fecha"),
                    "monto": pago.get("monto"),
                    "moneda": pago.get("moneda"),
                    "concepto": pago.get("concepto"),
                    "comprobante": pago.get("comprobante"),
                },
            )
        for aporte in (row.otros_aportes_no_iaavim or []):
            if not isinstance(aporte, dict):
                continue
            conn.execute(
                sa.text(
                    "INSERT INTO aportes_fomento "
                    "(tramite_id, organismo, programa, monto, moneda, created_at) "
                    "VALUES (:tramite_id, :organismo, :programa, :monto, :moneda, now())"
                ),
                {
                    "tramite_id": row.id,
                    "organismo": aporte.get("organismo"),
                    "programa": aporte.get("programa"),
                    "monto": aporte.get("monto"),
                    "moneda": aporte.get("moneda"),
                },
            )

    comites = conn.execute(
        sa.text(
            "SELECT id, integrantes FROM comites_fomento WHERE integrantes IS NOT NULL"
        )
    ).fetchall()
    evaluadores_validos = {
        row[0] for row in conn.execute(sa.text("SELECT id FROM evaluadores")).fetchall()
    }
    for row in comites:
        for integrante in (row.integrantes or []):
            if not isinstance(integrante, dict):
                continue
            evaluador_id = integrante.get("evaluador_id")
            # Si el JSON viejo tiene un evaluador_id inexistente (nunca se
            # validó antes), se omite en vez de fallar el backfill entero —
            # es exactamente el tipo de dato corrupto que este cambio busca
            # dejar de permitir hacia adelante.
            if evaluador_id is None or evaluador_id not in evaluadores_validos:
                print(
                    f"[fomento_relacional] comite {row.id}: evaluador_id "
                    f"{evaluador_id!r} inválido, se omite del backfill"
                )
                continue
            conn.execute(
                sa.text(
                    "INSERT INTO integrantes_comite (comite_id, evaluador_id, rol, created_at) "
                    "VALUES (:comite_id, :evaluador_id, :rol, now())"
                ),
                {"comite_id": row.id, "evaluador_id": evaluador_id, "rol": integrante.get("rol")},
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_integrantes_comite_evaluador_id", table_name="integrantes_comite")
    op.drop_index("ix_integrantes_comite_comite_id", table_name="integrantes_comite")
    op.drop_table("integrantes_comite")
    op.drop_index("ix_aportes_fomento_tramite_id", table_name="aportes_fomento")
    op.drop_table("aportes_fomento")
    op.drop_index("ix_pagos_fomento_tramite_id", table_name="pagos_fomento")
    op.drop_table("pagos_fomento")
