# models/__init__.py
# Importar todos los modelos para que SQLAlchemy los registre

from src.models.user_models import User, Role, UserRole, TokenRecovery
from src.models.training_models import Training
from src.models.work_models import Work, RolWork, TareaWork

# Modelos de formularios RePA
from src.models.persona_fisica_model import (
    PersonaFisica,
    SubperfilProductor,
    SubperfilDirector,
    SubperfilGuionista,
    SubperfilDocumentalista,
    SubperfilRealizadorIntegral,
    SubperfilTecnicoArtistico,
    SubperfilCapacitador,
    SubperfilInvestigador
)
from src.models.persona_juridica_model import PersonaJuridica, IntegrantePJ
from src.models.asociacion_model import Asociacion, IntegranteAsociacion
from src.models.obra_audiovisual_model import ObraAudiovisual, EquipoTecnicoObra

__all__ = [
    # User & Auth
    "User",
    "Role", 
    "UserRole",
    "TokenRecovery",
    # Training & Work
    "Training",
    "Work",
    "RolWork",
    "TareaWork",
    # Persona Física
    "PersonaFisica",
    "SubperfilProductor",
    "SubperfilDirector",
    "SubperfilGuionista",
    "SubperfilDocumentalista",
    "SubperfilRealizadorIntegral",
    "SubperfilTecnicoArtistico",
    "SubperfilCapacitador",
    "SubperfilInvestigador",
    # Persona Jurídica
    "PersonaJuridica",
    "IntegrantePJ",
    # Asociación
    "Asociacion",
    "IntegranteAsociacion",
    # Obras Audiovisuales (AGAM)
    "ObraAudiovisual",
    "EquipoTecnicoObra",
]
