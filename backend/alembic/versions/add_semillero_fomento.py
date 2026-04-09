"""add cohortes_semillero, participantes_semillero, acompanamientos_semillero tables

Revision ID: add_semillero_fomento
Revises: add_comites_dictamenes_fomento
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_semillero_fomento'
down_revision: Union[str, None] = 'add_comites_dictamenes_fomento'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cohortes_semillero',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('anio_edicion', sa.Integer(), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(), nullable=True),
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('cupo', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(50), nullable=False, server_default='planificada'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_cohortes_semillero_id', 'cohortes_semillero', ['id'])

    op.create_table(
        'participantes_semillero',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cohorte_id', sa.Integer(), sa.ForeignKey('cohortes_semillero.id'), nullable=False),
        sa.Column('codigo_repa', sa.String(50), nullable=True),
        sa.Column('nombre_completo', sa.String(255), nullable=True),
        sa.Column('distrito', sa.String(100), nullable=True),
        sa.Column('tramites_vinculados', sa.JSON(), nullable=True),
        sa.Column('diagnostico_inicial', sa.Text(), nullable=True),
        sa.Column('objetivos', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(50), nullable=False, server_default='activo'),
        sa.Column('resultados_cualitativos', sa.Text(), nullable=True),
        sa.Column('resultados_cuantificables', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_participantes_semillero_id', 'participantes_semillero', ['id'])
    op.create_index('ix_participantes_semillero_cohorte', 'participantes_semillero', ['cohorte_id'])

    op.create_table(
        'acompanamientos_semillero',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('participante_id', sa.Integer(), sa.ForeignKey('participantes_semillero.id'), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('fecha', sa.DateTime(), nullable=True),
        sa.Column('responsable', sa.String(255), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('adjuntos', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_acompanamientos_semillero_id', 'acompanamientos_semillero', ['id'])
    op.create_index('ix_acompanamientos_semillero_participante', 'acompanamientos_semillero', ['participante_id'])


def downgrade() -> None:
    op.drop_table('acompanamientos_semillero')
    op.drop_table('participantes_semillero')
    op.drop_table('cohortes_semillero')
