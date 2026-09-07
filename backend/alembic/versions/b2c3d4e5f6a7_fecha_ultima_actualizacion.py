"""padron: fecha_ultima_actualizacion en las entidades registrables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07

Hasta ahora no habia forma de responder "cuan al dia esta el dato que figura en
el padron". Habia fecha_envio (cuando se mando a revisar) y fecha_resolucion
(cuando el revisor decidio), pero nada que registrara la ultima vez que el
titular efectivamente modifico sus datos.

Va junto con el cambio que hace que editar un registro ya aprobado lo devuelva
a la cola de revision: las dos cosas responden a la misma regla de negocio, que
un dato publicado en el padron no cambia sin que alguien lo apruebe, y que se
sepa desde cuando rige.

NULL para las filas existentes: nunca se registro una actualizacion. Se llena
sola en la primera edicion de cada registro.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Las cinco entidades registrables del Padron RePA.
TABLAS = (
    "personas_fisicas",
    "personas_juridicas",
    "asociaciones",
    "estudiantes_esa",
    "obras_audiovisuales",
)


def upgrade() -> None:
    for tabla in TABLAS:
        op.add_column(
            tabla,
            sa.Column(
                "fecha_ultima_actualizacion",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for tabla in TABLAS:
        op.drop_column(tabla, "fecha_ultima_actualizacion")
