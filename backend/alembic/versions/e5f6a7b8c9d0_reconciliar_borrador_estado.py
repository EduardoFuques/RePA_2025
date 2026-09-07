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
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tablas que este backfill reconcilia, en el orden en que hay que hacerlo.
_TABLAS = (
    "personas_fisicas",
    "personas_juridicas",
    "estudiantes_esa",
    "asociaciones",
    "obras_audiovisuales",
)


def _hay_filas_inconsistentes(bind) -> bool:
    """Chequeo previo en SQL crudo, sin tocar los modelos ORM.

    Existe porque el backfill de abajo consulta los modelos, y SQLAlchemy arma
    el SELECT con las columnas mapeadas HOY: cualquier columna agregada al
    modelo despues de escrita esta migracion hace que correr las migraciones
    desde cero falle con UndefinedColumn. En una base nueva no hay nada que
    reconciliar, asi que ni siquiera hace falta llegar ahi; y en una base que ya
    aplico esta revision, no vuelve a ejecutarse.
    """
    import sqlalchemy as sa

    for tabla in _TABLAS:
        existe = bind.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = :t LIMIT 1"
            ),
            {"t": tabla},
        ).first()
        if not existe:
            continue
        fila = bind.execute(
            sa.text(
                f"SELECT 1 FROM {tabla} "  # noqa: S608 - nombre de una lista fija
                "WHERE borrador IS false AND estado = 'borrador' LIMIT 1"
            )
        ).first()
        if fila:
            return True
    return False


def upgrade() -> None:
    """Upgrade schema — backfill de datos, no cambia el esquema."""
    if not _hay_filas_inconsistentes(op.get_bind()):
        # Base nueva (o ya reconciliada): nada que hacer.
        return

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
            .filter(
                model.borrador.is_(False), model.estado == EstadoRegistro.borrador.value
            )
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
            .filter(
                model.borrador.is_(False), model.estado == EstadoRegistro.borrador.value
            )
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
