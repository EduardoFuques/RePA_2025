"""add missing sala/festival fields, agam timestamps, unify datetime pattern

Revision ID: add_sala_festival_agam_ts
Revises: add_semillero_fomento
Create Date: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sala_festival_agam_ts'
down_revision: Union[str, None] = 'add_constancia_rentas_pf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === SALA: nuevos campos ===
    op.add_column('salas', sa.Column('responsable_legal', sa.JSON(), nullable=True))
    op.add_column('salas', sa.Column('programador', sa.JSON(), nullable=True))
    op.add_column('salas', sa.Column('responsable_tecnico', sa.JSON(), nullable=True))
    op.add_column('salas', sa.Column('afiliaciones', sa.JSON(), nullable=True))
    op.add_column('salas', sa.Column('consentimiento', sa.Boolean(), server_default='false', nullable=False))

    # === FESTIVAL: nuevos campos ===
    op.add_column('festivales', sa.Column('periodicidad', sa.String(50), nullable=True))
    op.add_column('festivales', sa.Column('anio_inicio', sa.Integer(), nullable=True))
    op.add_column('festivales', sa.Column('responsable', sa.JSON(), nullable=True))
    op.add_column('festivales', sa.Column('curaduria', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('festivales', sa.Column('calendario_oficial', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('festivales', sa.Column('consentimiento', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('festivales', sa.Column('desea_recibir_info', sa.Boolean(), server_default='false', nullable=False))

    # === AGAM (obras_audiovisuales): agregar timestamps ===
    op.add_column('obras_audiovisuales', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
    op.add_column('obras_audiovisuales', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))


def downgrade() -> None:
    # === AGAM: quitar timestamps ===
    op.drop_column('obras_audiovisuales', 'updated_at')
    op.drop_column('obras_audiovisuales', 'created_at')

    # === FESTIVAL: quitar campos ===
    op.drop_column('festivales', 'desea_recibir_info')
    op.drop_column('festivales', 'consentimiento')
    op.drop_column('festivales', 'calendario_oficial')
    op.drop_column('festivales', 'curaduria')
    op.drop_column('festivales', 'responsable')
    op.drop_column('festivales', 'anio_inicio')
    op.drop_column('festivales', 'periodicidad')

    # === SALA: quitar campos ===
    op.drop_column('salas', 'consentimiento')
    op.drop_column('salas', 'afiliaciones')
    op.drop_column('salas', 'responsable_tecnico')
    op.drop_column('salas', 'programador')
    op.drop_column('salas', 'responsable_legal')
