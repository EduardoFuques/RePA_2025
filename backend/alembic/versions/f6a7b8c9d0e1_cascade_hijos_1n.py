"""cascade en hijos 1:N (subperfiles PF, integrantes PJ/AS, equipo técnico AGAM)

Antes, borrar una PersonaFisica/PersonaJuridica/Asociacion/ObraAudiovisual que
tuviera hijos (subperfiles, integrantes, equipo técnico) fallaba con
IntegrityError sin manejar — los DELETE /me de esos 4 formularios están
expuestos desde hace tiempo pero nunca funcionaron si había hijos cargados
por fuera de la sesión de SQLAlchemy actual (el cascade del ORM
`delete-orphan` no cubre ese caso; hace falta ON DELETE CASCADE en la DB).

Busca el nombre real de cada constraint vía information_schema en vez de
asumir el nombre autogenerado por Postgres, para no romper si en algún
momento se creó con un nombre distinto al default.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabla_hijo, columna_fk, tabla_padre)
RELACIONES_CASCADE = [
    ("subperfil_productor", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_director", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_guionista", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_documentalista", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_realizador_integral", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_tecnico_artistico", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_capacitador", "persona_fisica_id", "personas_fisicas"),
    ("subperfil_investigador", "persona_fisica_id", "personas_fisicas"),
    ("integrantes_pj", "persona_juridica_id", "personas_juridicas"),
    ("integrantes_asociacion", "asociacion_id", "asociaciones"),
    ("equipo_tecnico_obra", "obra_id", "obras_audiovisuales"),
]


def _find_fk_name(conn, tabla_hijo: str, columna: str) -> str | None:
    row = conn.execute(
        sa.text(
            """
            SELECT tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = :tabla
                AND kcu.column_name = :columna
                AND tc.table_schema = current_schema()
            """
        ),
        {"tabla": tabla_hijo, "columna": columna},
    ).first()
    return row[0] if row else None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for tabla_hijo, columna, tabla_padre in RELACIONES_CASCADE:
        nombre = _find_fk_name(conn, tabla_hijo, columna)
        if nombre is None:
            # Ya no existe (o nunca existió con ese nombre) — no romper el
            # deploy por esto, solo lo dejamos asentado en el log de alembic.
            print(f"[cascade_hijos_1n] FK no encontrada: {tabla_hijo}.{columna} — se omite")
            continue
        op.drop_constraint(nombre, tabla_hijo, type_="foreignkey")
        op.create_foreign_key(
            nombre, tabla_hijo, tabla_padre, [columna], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    for tabla_hijo, columna, tabla_padre in RELACIONES_CASCADE:
        nombre = _find_fk_name(conn, tabla_hijo, columna)
        if nombre is None:
            continue
        op.drop_constraint(nombre, tabla_hijo, type_="foreignkey")
        op.create_foreign_key(nombre, tabla_hijo, tabla_padre, [columna], ["id"])
