"""reconciliar borrador vs estado + backfill de codigo_repa (Fase 3b)

Antes de que el envío emitiera el código RePA (Fase 3a), cualquier fila con
borrador=False pero estado='borrador' quedó en un estado inconsistente (A9
del informe de auditoría): "enviada" según el bool pero "borrador" según el
lifecycle, sin código asignado. Este backfill de una sola vez:

1. PF, PJ, ESA: para cada fila borrador=False / estado='borrador', la pasa a
   'enviado' y le emite código propio si no tiene (reusa
   lifecycle_service/repa_code_service reales, no duplica la lógica).
2. AS, AGAM: ídem la transición de estado, y les copia el código de la
   Persona Física titular como codigo_repa_titular.

De acá en más (Fase 3a) borrador y estado siempre se mueven juntos en el
envío, así que este desvío no debería volver a producirse — es un backfill
histórico, no una reconciliación permanente.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — backfill de datos, no cambia el esquema."""
    from src.models.asociacion_model import Asociacion
    from src.models.esa_model import EstudianteESA
    from src.models.obra_audiovisual_model import ObraAudiovisual
    from src.models.persona_fisica_model import PersonaFisica
    from src.models.persona_juridica_model import PersonaJuridica
    from src.models.registro_lifecycle import EstadoRegistro
    from src.services import lifecycle_service

    bind = op.get_bind()
    db = Session(bind=bind)

    # 1) PF/PJ/ESA: código propio.
    for model in (PersonaFisica, PersonaJuridica, EstudianteESA):
        inconsistentes = (
            db.query(model)
            .filter(model.borrador.is_(False), model.estado == EstadoRegistro.borrador.value)
            .all()
        )
        for registro in inconsistentes:
            lifecycle_service.enviar_a_revision(db, registro)
            lifecycle_service.emitir_codigo_repa_propio(db, registro)
    db.commit()

    # 2) AS/AGAM: heredan el código de la PF titular (ya reconciliada arriba).
    for model in (Asociacion, ObraAudiovisual):
        inconsistentes = (
            db.query(model)
            .filter(model.borrador.is_(False), model.estado == EstadoRegistro.borrador.value)
            .all()
        )
        for registro in inconsistentes:
            pf = (
                db.query(PersonaFisica)
                .filter(PersonaFisica.user_id == registro.user_id)
                .first()
            )
            lifecycle_service.enviar_a_revision(db, registro)
            lifecycle_service.heredar_codigo_repa_titular(db, registro, pf)
    db.commit()


def downgrade() -> None:
    """No reversible: es un backfill de datos históricos, no un cambio de esquema."""
    pass
