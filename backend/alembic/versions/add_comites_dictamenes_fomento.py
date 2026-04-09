"""add comites_fomento and dictamenes_fomento tables

Revision ID: add_comites_dictamenes_fomento
Revises: add_eventos_lineas_fomento
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_comites_dictamenes_fomento'
down_revision: Union[str, None] = 'add_eventos_lineas_fomento'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'comites_fomento',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('evento_id', sa.Integer(), sa.ForeignKey('eventos_fomento.id'), nullable=False),
        sa.Column('linea_id', sa.Integer(), sa.ForeignKey('lineas_fomento.id'), nullable=True),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('nombre', sa.String(255), nullable=True),
        sa.Column('integrantes', sa.JSON(), nullable=True),
        sa.Column('resolucion_designacion_path', sa.String(500), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_comites_fomento_id', 'comites_fomento', ['id'])
    op.create_index('ix_comites_fomento_evento', 'comites_fomento', ['evento_id'])

    op.create_table(
        'dictamenes_fomento',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tramite_id', sa.Integer(), sa.ForeignKey('tramites_fomento.id'), nullable=False),
        sa.Column('comite_id', sa.Integer(), sa.ForeignKey('comites_fomento.id'), nullable=True),
        sa.Column('evaluador_id', sa.Integer(), sa.ForeignKey('evaluadores.id'), nullable=False),
        sa.Column('tipo_dictamen', sa.String(50), nullable=False),
        sa.Column('fecha', sa.DateTime(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('puntaje', sa.Integer(), nullable=True),
        sa.Column('archivo_pdf_path', sa.String(500), nullable=True),
        sa.Column('devolucion_presentante', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('devolucion_archivo_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_dictamenes_fomento_id', 'dictamenes_fomento', ['id'])
    op.create_index('ix_dictamenes_fomento_tramite', 'dictamenes_fomento', ['tramite_id'])
    op.create_index('ix_dictamenes_fomento_evaluador', 'dictamenes_fomento', ['evaluador_id'])


def downgrade() -> None:
    op.drop_table('dictamenes_fomento')
    op.drop_table('comites_fomento')
