# models/__init__.py
# Importar todos los modelos para que SQLAlchemy los registre

from src.models.asociacion_model import Asociacion, IntegranteAsociacion

# Audit Trail
from src.models.audit_model import AuditAction, AuditLog

# Modelos ESA y Exhibiciones
from src.models.esa_model import EstudianteESA
from src.models.exhibicion_model import Cinemateca, Exhibicion, Festival, Sala
from src.models.obra_audiovisual_model import EquipoTecnicoObra, ObraAudiovisual

# Modelos de formularios RePA
from src.models.persona_fisica_model import (
    PersonaFisica,
    SubperfilCapacitador,
    SubperfilDirector,
    SubperfilDocumentalista,
    SubperfilGuionista,
    SubperfilInvestigador,
    SubperfilProductor,
    SubperfilRealizadorIntegral,
    SubperfilTecnicoArtistico,
)
from src.models.persona_juridica_model import IntegrantePJ, PersonaJuridica

# Comisión de Filmaciones
from src.models.rodaje_model import Rodaje
from src.models.user_models import Role, TokenRecovery, User, UserRole

__all__ = [
    # User & Auth
    "User",
    "Role",
    "UserRole",
    "TokenRecovery",
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
    # ESA (Estudiantes)
    "EstudianteESA",
    # Exhibiciones
    "Sala",
    "Exhibicion",
    "Festival",
    "Cinemateca",
    # Comisión de Filmaciones
    "Rodaje",
    # Audit Trail
    "AuditLog",
    "AuditAction",
]
