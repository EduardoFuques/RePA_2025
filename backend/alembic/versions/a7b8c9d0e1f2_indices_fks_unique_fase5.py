"""Fase 5: índices faltantes, FKs reales de fomento, unicidad dni/cuit

Cierra tres huecos de integridad encontrados en la auditoría pre-producción:

1. Índices ausentes en columnas por las que el backoffice filtra/pagina todo
   el tiempo (``estado`` del lifecycle en PF/PJ/AS/AGAM/ESA, y ``user_id`` en
   las 8 tablas 1:N que hoy se recorren con scan secuencial en cada "Mis
   Registros"/admin).
2. ``tramites_fomento.evento_id/linea_id/cohorte_semillero_id`` eran
   ``Integer`` sueltos sin FK: permitían quedar apuntando a un evento/línea/
   cohorte borrado o inexistente. Los modelos ya se actualizaron a
   ``ForeignKey`` real; esta migración crea la constraint en la base.
3. ``evaluadores.dni`` y ``asociaciones.cuit`` sin unicidad: dos evaluadores
   o dos asociaciones podían cargarse con el mismo documento/CUIT sin que la
   base lo objete.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tablas que usan RegistroLifecycleMixin (columna `estado`).
TABLAS_LIFECYCLE = [
    "personas_fisicas",
    "personas_juridicas",
    "asociaciones",
    "obras_audiovisuales",
    "estudiantes_esa",
]

# (tabla, columna) para índices sueltos de user_id.
INDICES_USER_ID = [
    ("salas", "user_id"),
    ("exhibiciones", "user_id"),
    ("festivales", "user_id"),
    ("rodajes", "user_id"),
    ("tramites_fomento", "user_id"),
    ("evaluadores", "user_id"),
    ("obras_audiovisuales", "user_id"),
    ("audit_logs", "user_id"),
]


def upgrade() -> None:
    """Upgrade schema."""
    for tabla in TABLAS_LIFECYCLE:
        op.create_index(f"ix_{tabla}_estado", tabla, ["estado"])

    for tabla, columna in INDICES_USER_ID:
        op.create_index(f"ix_{tabla}_{columna}", tabla, [columna])

    op.create_foreign_key(
        "fk_tramites_fomento_evento_id",
        "tramites_fomento",
        "eventos_fomento",
        ["evento_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_tramites_fomento_linea_id",
        "tramites_fomento",
        "lineas_fomento",
        ["linea_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_tramites_fomento_cohorte_semillero_id",
        "tramites_fomento",
        "cohortes_semillero",
        ["cohorte_semillero_id"],
        ["id"],
    )

    op.create_unique_constraint("uq_evaluadores_dni", "evaluadores", ["dni"])
    op.create_unique_constraint("uq_asociaciones_cuit", "asociaciones", ["cuit"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_asociaciones_cuit", "asociaciones", type_="unique")
    op.drop_constraint("uq_evaluadores_dni", "evaluadores", type_="unique")

    op.drop_constraint(
        "fk_tramites_fomento_cohorte_semillero_id", "tramites_fomento", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tramites_fomento_linea_id", "tramites_fomento", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_tramites_fomento_evento_id", "tramites_fomento", type_="foreignkey"
    )

    for tabla, columna in INDICES_USER_ID:
        op.drop_index(f"ix_{tabla}_{columna}", table_name=tabla)

    for tabla in TABLAS_LIFECYCLE:
        op.drop_index(f"ix_{tabla}_estado", table_name=tabla)
