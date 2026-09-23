"""Borrador en expedientes e instrumentos juridicos

Habilita el autoguardado en los dos modulos de area, con el mismo patron que
ya usan los formularios del Padron y el de rodajes: la fila se crea apenas se
escribe el primer campo y queda marcada como borrador hasta que el area la da
por cargada.

Sin esto, el formulario del frontend no podia autoguardar instrumentos:
tipo_documento, titulo, resumen y archivo_pdf_path eran NOT NULL, asi que la
primera llamada fallaba hasta tener los cuatro completos. La obligatoriedad no
desaparece — se mueve al momento de ENVIAR (borrador=False), que es donde el
formulario del area realmente la necesita, y la valida la ruta devolviendo 422
con la lista de campos que faltan.

Expedientes ya tenia todas sus columnas nullable, asi que ahi solo se suma la
marca de borrador, por consistencia y para que el listado pueda distinguir una
carga a medio hacer de una terminada.

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-09-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = ("expedientes_administrativos", "instrumentos_juridicos")

# Los que dejan de ser NOT NULL para poder guardarse a medias.
COLUMNAS_INSTRUMENTOS = (
    ("tipo_documento", sa.String(length=50)),
    ("titulo", sa.String(length=500)),
    ("resumen", sa.Text()),
    ("archivo_pdf_path", sa.String(length=500)),
)


def upgrade() -> None:
    for tabla in TABLAS:
        # server_default es obligatorio para crear una columna NOT NULL sobre
        # una tabla que ya puede tener filas: sin el, Postgres no sabe que
        # poner en las existentes.
        op.add_column(
            tabla,
            sa.Column(
                "borrador",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
        # Y se quita enseguida: el modelo declara `default=False` del lado de
        # Python, no server_default. Si quedara, `alembic check` detectaria
        # drift en cada corrida.
        op.alter_column(tabla, "borrador", server_default=None)

    for columna, tipo in COLUMNAS_INSTRUMENTOS:
        op.alter_column(
            "instrumentos_juridicos",
            columna,
            existing_type=tipo,
            nullable=True,
        )


def downgrade() -> None:
    # Volver a NOT NULL exige que no queden borradores a medio cargar: se
    # rellenan con un texto explicito antes de restaurar la restriccion, para
    # que el downgrade no falle sobre datos reales.
    conexion = op.get_bind()
    for columna, _tipo in COLUMNAS_INSTRUMENTOS:
        relleno = "" if columna == "resumen" else "(sin dato)"
        conexion.execute(
            sa.text(
                f"UPDATE instrumentos_juridicos SET {columna} = :relleno "
                f"WHERE {columna} IS NULL"
            ),
            {"relleno": relleno or "(sin dato)"},
        )

    for columna, tipo in COLUMNAS_INSTRUMENTOS:
        op.alter_column(
            "instrumentos_juridicos",
            columna,
            existing_type=tipo,
            nullable=False,
        )

    for tabla in TABLAS:
        op.drop_column(tabla, "borrador")
