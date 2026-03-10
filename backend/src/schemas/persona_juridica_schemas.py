# schemas/persona_juridica_schemas.py
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# === INTEGRANTE ===
class IntegrantePJBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dni: str | None = Field(None, max_length=20)
    cargo: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    vinculado_repa: bool = False


class IntegrantePJCreate(IntegrantePJBase):
    pass


class IntegrantePJOut(IntegrantePJBase):
    id: int
    persona_juridica_id: int

    model_config = ConfigDict(from_attributes=True)


# === SCHEMA PRINCIPAL ===
class PersonaJuridicaCreate(BaseModel):
    """Schema para crear una Persona Jurídica"""

    declaracion_inicial: bool = True

    # Datos institucionales - permitidos null para borradores
    nombre_pj: str | None = Field(None, max_length=255)
    cuit: str | None = Field(None, max_length=15)
    figura_legal: str | None = Field(None, max_length=50)
    otra_figura_legal: str | None = Field(None, max_length=100)
    fecha_constitucion: date | None = None
    objeto_social: str | None = None

    # Domicilio y contacto
    domicilio_legal: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    telefono_institucional: str | None = Field(None, max_length=30)
    email_contacto: EmailStr | None = None
    web_redes: list[str] | None = None

    # Representación legal
    nombre_representante: str | None = Field(None, max_length=200)
    dni_representante: str | None = Field(None, max_length=20)
    cargo_representante: str | None = Field(None, max_length=100)
    telefono_representante: str | None = Field(None, max_length=30)
    email_representante: EmailStr | None = None
    vincular_personas: str | None = None

    # Actividades audiovisuales
    actividades_principales: list[str] | None = None
    otra_actividad: str | None = None
    lineas_trabajo: str | None = None
    apoyo_iaavim: str | None = None
    descripcion_apoyo: str | None = None
    otros_registros: str | None = None
    cuales_registros: str | None = None

    # Documentación (paths)
    estatuto_path: str | None = None
    constancia_cuit_path: str | None = None
    acta_autoridades_path: str | None = None
    cv_institucional_path: str | None = None

    # Consentimiento
    consentimiento: bool = False
    borrador: bool = False


class PersonaJuridicaUpdate(BaseModel):
    """Schema para actualizar una Persona Jurídica"""

    # Datos institucionales
    nombre_pj: str | None = Field(None, max_length=255)
    cuit: str | None = Field(None, max_length=15)
    figura_legal: str | None = Field(None, max_length=50)
    otra_figura_legal: str | None = Field(None, max_length=100)
    fecha_constitucion: date | None = None
    objeto_social: str | None = None

    # Domicilio y contacto
    domicilio_legal: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    telefono_institucional: str | None = Field(None, max_length=30)
    email_contacto: EmailStr | None = None
    web_redes: list[str] | None = None

    # Representación legal
    nombre_representante: str | None = Field(None, max_length=200)
    dni_representante: str | None = Field(None, max_length=20)
    cargo_representante: str | None = Field(None, max_length=100)
    telefono_representante: str | None = Field(None, max_length=30)
    email_representante: EmailStr | None = None
    vincular_personas: str | None = None

    # Actividades audiovisuales
    actividades_principales: list[str] | None = None
    otra_actividad: str | None = None
    lineas_trabajo: str | None = None
    apoyo_iaavim: str | None = None
    descripcion_apoyo: str | None = None
    otros_registros: str | None = None
    cuales_registros: str | None = None

    # Documentación (paths)
    estatuto_path: str | None = None
    constancia_cuit_path: str | None = None
    acta_autoridades_path: str | None = None
    cv_institucional_path: str | None = None

    consentimiento: bool | None = None
    declaracion_inicial: bool | None = None
    borrador: bool | None = None


class PersonaJuridicaOut(BaseModel):
    """Schema de salida para Persona Jurídica"""

    id: int
    user_id: str

    # Datos institucionales
    nombre_pj: str | None = None
    cuit: str | None = None
    figura_legal: str | None = None
    otra_figura_legal: str | None = None
    fecha_constitucion: date | None = None
    objeto_social: str | None = None

    # Domicilio y contacto
    domicilio_legal: str | None = None
    localidad: str | None = None
    distrito: str | None = None
    telefono_institucional: str | None = None
    email_contacto: str | None = None
    web_redes: list[str] | None = None

    # Representación legal
    nombre_representante: str | None = None
    dni_representante: str | None = None
    cargo_representante: str | None = None
    telefono_representante: str | None = None
    email_representante: str | None = None
    vincular_personas: str | None = None

    # Actividades audiovisuales
    actividades_principales: list[str] | None = None
    otra_actividad: str | None = None
    lineas_trabajo: str | None = None
    apoyo_iaavim: str | None = None
    descripcion_apoyo: str | None = None
    otros_registros: str | None = None
    cuales_registros: str | None = None

    # Documentación (paths)
    estatuto_path: str | None = None
    constancia_cuit_path: str | None = None
    acta_autoridades_path: str | None = None
    cv_institucional_path: str | None = None

    # Consentimiento
    consentimiento: bool
    declaracion_inicial: bool
    borrador: bool

    # Metadatos
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Integrantes
    integrantes: list[IntegrantePJOut] = []

    model_config = ConfigDict(from_attributes=True)
