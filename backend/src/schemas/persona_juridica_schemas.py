# schemas/persona_juridica_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# === INTEGRANTE ===
class IntegrantePJBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dni: Optional[str] = Field(None, max_length=20)
    cargo: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
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
    
    # Datos institucionales
    nombre_pj: str = Field(..., min_length=1, max_length=255)
    cuit: str = Field(..., min_length=1, max_length=15)
    figura_legal: str = Field(..., min_length=1, max_length=50)
    otra_figura_legal: Optional[str] = Field(None, max_length=100)
    fecha_constitucion: Optional[date] = None
    objeto_social: Optional[str] = None
    
    # Domicilio y contacto
    domicilio_legal: str = Field(..., min_length=1, max_length=255)
    localidad: str = Field(..., min_length=1, max_length=100)
    distrito: str = Field(..., min_length=1, max_length=50)
    telefono_institucional: str = Field(..., min_length=1, max_length=30)
    email_contacto: EmailStr
    web_redes: Optional[List[str]] = None
    
    # Representación legal
    nombre_representante: str = Field(..., min_length=1, max_length=200)
    dni_representante: str = Field(..., min_length=1, max_length=20)
    cargo_representante: str = Field(..., min_length=1, max_length=100)
    telefono_representante: str = Field(..., min_length=1, max_length=30)
    email_representante: EmailStr
    vincular_personas: Optional[str] = None
    
    # Actividades audiovisuales
    actividades_principales: Optional[List[str]] = None
    otra_actividad: Optional[str] = None
    lineas_trabajo: Optional[str] = None
    apoyo_iaavim: Optional[str] = None
    descripcion_apoyo: Optional[str] = None
    otros_registros: Optional[str] = None
    cuales_registros: Optional[str] = None
    
    # Consentimiento
    consentimiento: bool = False


class PersonaJuridicaUpdate(BaseModel):
    """Schema para actualizar una Persona Jurídica"""
    # Datos institucionales
    nombre_pj: Optional[str] = Field(None, max_length=255)
    figura_legal: Optional[str] = Field(None, max_length=50)
    otra_figura_legal: Optional[str] = Field(None, max_length=100)
    fecha_constitucion: Optional[date] = None
    objeto_social: Optional[str] = None
    
    # Domicilio y contacto
    domicilio_legal: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    telefono_institucional: Optional[str] = Field(None, max_length=30)
    email_contacto: Optional[EmailStr] = None
    web_redes: Optional[List[str]] = None
    
    # Representación legal
    nombre_representante: Optional[str] = Field(None, max_length=200)
    dni_representante: Optional[str] = Field(None, max_length=20)
    cargo_representante: Optional[str] = Field(None, max_length=100)
    telefono_representante: Optional[str] = Field(None, max_length=30)
    email_representante: Optional[EmailStr] = None
    vincular_personas: Optional[str] = None
    
    # Actividades audiovisuales
    actividades_principales: Optional[List[str]] = None
    otra_actividad: Optional[str] = None
    lineas_trabajo: Optional[str] = None
    apoyo_iaavim: Optional[str] = None
    descripcion_apoyo: Optional[str] = None
    otros_registros: Optional[str] = None
    cuales_registros: Optional[str] = None


class PersonaJuridicaOut(BaseModel):
    """Schema de salida para Persona Jurídica"""
    id: int
    user_id: str
    
    # Datos institucionales
    nombre_pj: str
    cuit: str
    figura_legal: str
    otra_figura_legal: Optional[str] = None
    fecha_constitucion: Optional[date] = None
    objeto_social: Optional[str] = None
    
    # Domicilio y contacto
    domicilio_legal: str
    localidad: str
    distrito: str
    telefono_institucional: str
    email_contacto: str
    web_redes: Optional[List[str]] = None
    
    # Representación legal
    nombre_representante: str
    dni_representante: str
    cargo_representante: str
    telefono_representante: str
    email_representante: str
    vincular_personas: Optional[str] = None
    
    # Actividades audiovisuales
    actividades_principales: Optional[List[str]] = None
    otra_actividad: Optional[str] = None
    lineas_trabajo: Optional[str] = None
    apoyo_iaavim: Optional[str] = None
    descripcion_apoyo: Optional[str] = None
    otros_registros: Optional[str] = None
    cuales_registros: Optional[str] = None
    
    # Documentación (paths)
    estatuto_path: Optional[str] = None
    constancia_cuit_path: Optional[str] = None
    acta_autoridades_path: Optional[str] = None
    cv_institucional_path: Optional[str] = None
    
    # Consentimiento
    consentimiento: bool
    declaracion_inicial: bool
    
    # Metadatos
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Integrantes
    integrantes: List[IntegrantePJOut] = []
    
    model_config = ConfigDict(from_attributes=True)
