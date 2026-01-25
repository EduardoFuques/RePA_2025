# schemas/asociacion_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# === INTEGRANTE ===
class IntegranteAsociacionBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dni: Optional[str] = Field(None, max_length=20)
    rol: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    vinculado_repa: bool = False

class IntegranteAsociacionCreate(IntegranteAsociacionBase):
    pass

class IntegranteAsociacionOut(IntegranteAsociacionBase):
    id: int
    asociacion_id: int
    
    model_config = ConfigDict(from_attributes=True)

# === SCHEMA PRINCIPAL ===
class AsociacionCreate(BaseModel):
    """Schema para crear una Asociación/Colectivo"""
    declaracion_inicial: bool = True
    
    # Datos básicos y contacto
    nombre_asociacion: str = Field(..., min_length=1, max_length=255)
    anio_creacion: Optional[int] = None
    personeria_juridica: Optional[str] = None
    tipo_personeria: Optional[str] = None
    otra_personeria: Optional[str] = None
    cuit: Optional[str] = Field(None, max_length=15)
    domicilio: str = Field(..., min_length=1, max_length=255)
    localidad: str = Field(..., min_length=1, max_length=100)
    distrito: str = Field(..., min_length=1, max_length=50)
    telefono: Optional[str] = Field(None, max_length=30)
    email: EmailStr
    web: Optional[str] = Field(None, max_length=500)
    
    # Representación
    nombre_referente: str = Field(..., min_length=1, max_length=200)
    rol_referente: Optional[str] = Field(None, max_length=100)
    telefono_referente: Optional[str] = Field(None, max_length=30)
    email_referente: Optional[EmailStr] = None
    
    # Ámbitos de actuación
    ambito_produccion: bool = False
    ambito_formacion: bool = False
    ambito_exhibicion: bool = False
    ambito_comunicacion: bool = False
    ambito_distribucion: bool = False
    ambito_comunidad: bool = False
    ambito_investigacion: bool = False
    ambito_otro: bool = False
    otro_ambito: Optional[str] = None
    
    # Objetivos e integrantes
    objetivos: Optional[str] = None
    cantidad_integrantes: Optional[int] = None
    articulo_iaavim: Optional[str] = None
    descripcion_articulacion: Optional[str] = None
    info_adicional_integrantes: Optional[str] = None
    
    # Consentimiento
    consentimiento: bool = False


class AsociacionUpdate(BaseModel):
    """Schema para actualizar una Asociación/Colectivo"""
    # Datos básicos y contacto
    nombre_asociacion: Optional[str] = Field(None, max_length=255)
    anio_creacion: Optional[int] = None
    personeria_juridica: Optional[str] = None
    tipo_personeria: Optional[str] = None
    otra_personeria: Optional[str] = None
    cuit: Optional[str] = Field(None, max_length=15)
    domicilio: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    telefono: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    web: Optional[str] = Field(None, max_length=500)
    
    # Representación
    nombre_referente: Optional[str] = Field(None, max_length=200)
    rol_referente: Optional[str] = Field(None, max_length=100)
    telefono_referente: Optional[str] = Field(None, max_length=30)
    email_referente: Optional[EmailStr] = None
    
    # Ámbitos de actuación
    ambito_produccion: Optional[bool] = None
    ambito_formacion: Optional[bool] = None
    ambito_exhibicion: Optional[bool] = None
    ambito_comunicacion: Optional[bool] = None
    ambito_distribucion: Optional[bool] = None
    ambito_comunidad: Optional[bool] = None
    ambito_investigacion: Optional[bool] = None
    ambito_otro: Optional[bool] = None
    otro_ambito: Optional[str] = None
    
    # Objetivos e integrantes
    objetivos: Optional[str] = None
    cantidad_integrantes: Optional[int] = None
    articulo_iaavim: Optional[str] = None
    descripcion_articulacion: Optional[str] = None
    info_adicional_integrantes: Optional[str] = None


class AsociacionOut(BaseModel):
    """Schema de salida para Asociación/Colectivo"""
    id: int
    user_id: str
    
    # Datos básicos y contacto
    nombre_asociacion: str
    anio_creacion: Optional[int] = None
    personeria_juridica: Optional[str] = None
    tipo_personeria: Optional[str] = None
    otra_personeria: Optional[str] = None
    cuit: Optional[str] = None
    domicilio: str
    localidad: str
    distrito: str
    telefono: Optional[str] = None
    email: str
    web: Optional[str] = None
    
    # Representación
    nombre_referente: str
    rol_referente: Optional[str] = None
    telefono_referente: Optional[str] = None
    email_referente: Optional[str] = None
    
    # Ámbitos de actuación
    ambito_produccion: bool
    ambito_formacion: bool
    ambito_exhibicion: bool
    ambito_comunicacion: bool
    ambito_distribucion: bool
    ambito_comunidad: bool
    ambito_investigacion: bool
    ambito_otro: bool
    otro_ambito: Optional[str] = None
    
    # Objetivos e integrantes
    objetivos: Optional[str] = None
    cantidad_integrantes: Optional[int] = None
    articulo_iaavim: Optional[str] = None
    descripcion_articulacion: Optional[str] = None
    info_adicional_integrantes: Optional[str] = None
    
    # Documentación (paths)
    acta_constitucion_path: Optional[str] = None
    declaracion_objetivos_path: Optional[str] = None
    
    # Consentimiento
    consentimiento: bool
    declaracion_inicial: bool
    
    # Metadatos
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Integrantes
    integrantes: List[IntegranteAsociacionOut] = []
    
    model_config = ConfigDict(from_attributes=True)
