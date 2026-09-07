"""revocacion de sesiones: users.token_version

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-09-07

Hasta ahora no habia forma de revocar una sesion. `create_access_token`
generaba un `jti` que no se guardaba ni se consultaba, y no existe logout del
lado del servidor: cambiar la contrasena —por autoservicio o por el circuito de
recuperacion por email— NO invalidaba los tokens ya emitidos. Quien tuviera el
refresh token seguia renovando su sesion siete dias aunque la victima cambiara
la clave.

`token_version` es la generacion de sesiones del usuario. Cada token lleva ese
numero en el claim `tv`; cambiar la contrasena lo incrementa y todos los tokens
anteriores dejan de valer.

Es un contador y no una marca de tiempo a proposito. Con un timestamp habria
que comparar contra el `iat` del JWT, que tiene resolucion de un segundo, y esa
ambiguedad no se puede resolver: con margen hacia adelante se rechaza el token
del re-login inmediato (el usuario no puede volver a entrar despues de cambiar
su clave), y sin margen sobrevive el token emitido en el mismo segundo del
cambio (la revocacion no revoca). Las dos variantes se probaron y las dos
fallaron, cada una en un test distinto.

Las filas existentes arrancan en 0. Los tokens emitidos antes de este deploy no
traen el claim `tv` y se aceptan hasta expirar solos (30 minutos los de acceso,
7 dias los de refresco), para no desloguear a todo el mundo durante el
despliegue.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
