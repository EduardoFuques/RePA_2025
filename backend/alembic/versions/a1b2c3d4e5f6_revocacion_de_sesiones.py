"""revocacion de sesiones: users.tokens_valid_from

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-09-07

Hasta ahora no habia forma de revocar una sesion. `create_access_token`
generaba un `jti` que no se guardaba ni se consultaba, y no existia logout del
lado del servidor: cambiar la contrasena —por autoservicio o por el circuito de
recuperacion por email— NO invalidaba los tokens ya emitidos. Quien tuviera el
refresh token seguia renovando su sesion siete dias aunque la victima cambiara
la clave.

`tokens_valid_from` es un sello por usuario: todo token cuyo `iat` sea anterior
se rechaza. Cambiar la contrasena adelanta el sello y con eso caen todas las
sesiones abiertas de esa cuenta.

NULL para las filas existentes = nunca se revoco nada, los tokens vigentes
siguen valiendo. Los tokens emitidos antes de este deploy no traen `iat` y se
aceptan hasta que expiren solos (30 minutos los de acceso, 7 dias los de
refresco), para no desloguear a todo el mundo durante el despliegue.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("tokens_valid_from", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "tokens_valid_from")
