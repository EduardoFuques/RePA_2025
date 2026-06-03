"""add esa document paths

Agrega columnas para persistir los adjuntos del registro de Estudiante ESA
(certificado de alumno regular y copia de DNI), que antes el frontend enviaba
pero el backend descartaba por no existir en el modelo/schema.

Revision ID: a1b2c3d4e5f6
Revises: 69cbe6e11c32
Create Date: 2026-06-03 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '69cbe6e11c32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'estudiantes_esa',
        sa.Column('certificado_alumno_path', sa.String(length=500), nullable=True),
    )
    op.add_column(
        'estudiantes_esa',
        sa.Column('copia_dni_path', sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('estudiantes_esa', 'copia_dni_path')
    op.drop_column('estudiantes_esa', 'certificado_alumno_path')
