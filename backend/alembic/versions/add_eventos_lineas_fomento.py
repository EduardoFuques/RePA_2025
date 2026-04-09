"""add eventos_fomento and lineas_fomento tables

Revision ID: add_eventos_lineas_fomento
Revises: add_otros_documentos_fomento
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_eventos_lineas_fomento'
down_revision: Union[str, None] = 'add_otros_documentos_fomento'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'eventos_fomento',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('anio_edicion', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('estado', sa.String(30), nullable=False, server_default='borrador'),
        sa.Column('fecha_apertura', sa.DateTime(), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(), nullable=True),
        sa.Column('bases_condiciones_path', sa.String(500), nullable=True),
        sa.Column('presupuesto_global', sa.Integer(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'lineas_fomento',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('evento_id', sa.Integer(), sa.ForeignKey('eventos_fomento.id'), nullable=False),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('vigente', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('tope_por_proyecto', sa.Integer(), nullable=True),
        sa.Column('moneda_tope', sa.String(10), nullable=True),
        sa.Column('cupo', sa.Integer(), nullable=True),
        sa.Column('requiere_evaluacion', sa.Boolean(), server_default='1'),
        sa.Column('tipo_comite', sa.String(50), nullable=True),
        sa.Column('documentacion_requerida', sa.JSON(), nullable=True),
        sa.Column('campos_especificos', sa.JSON(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('lineas_fomento')
    op.drop_table('eventos_fomento')
