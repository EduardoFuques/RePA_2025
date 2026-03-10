# schemas/asociacion_schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# === INTEGRANTE ===
class IntegranteAsociacionBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dni: str | None = Field(None, max_length=20)
    rol: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
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

    # Datos básicos y contacto - permitidos null para borradores
    nombre_asociacion: str | None = Field(None, max_length=255)
    anio_creacion: int | None = None
    personeria_juridica: str | None = None
    tipo_personeria: str | None = None
    otra_personeria: str | None = None
    cuit: str | None = Field(None, max_length=15)
    domicilio: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    telefono: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    web: str | None = Field(None, max_length=500)

    # Representación
    nombre_referente: str | None = Field(None, max_length=200)
    rol_referente: str | None = Field(None, max_length=100)
    telefono_referente: str | None = Field(None, max_length=30)
    email_referente: EmailStr | None = None

    # Ámbitos de actuación
    ambito_produccion: bool = False
    ambito_formacion: bool = False
    ambito_exhibicion: bool = False
    ambito_comunicacion: bool = False
    ambito_distribucion: bool = False
    ambito_comunidad: bool = False
    ambito_investigacion: bool = False
    ambito_otro: bool = False
    otro_ambito: str | None = None

    # Objetivos e integrantes
    objetivos: str | None = None
    cantidad_integrantes: int | None = None
    articulo_iaavim: str | None = None
    descripcion_articulacion: str | None = None
    info_adicional_integrantes: str | None = None

    # Documentación
    acta_constitucion_path: str | None = None
    declaracion_objetivos_path: str | None = None

    # Consentimiento
    consentimiento: bool = False
    borrador: bool = False


class AsociacionUpdate(BaseModel):
    """Schema para actualizar una Asociación/Colectivo"""

    # Datos básicos y contacto
    nombre_asociacion: str | None = Field(None, max_length=255)
    anio_creacion: int | None = None
    personeria_juridica: str | None = None
    tipo_personeria: str | None = None
    otra_personeria: str | None = None
    cuit: str | None = Field(None, max_length=15)
    domicilio: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    telefono: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    web: str | None = Field(None, max_length=500)

    # Representación
    nombre_referente: str | None = Field(None, max_length=200)
    rol_referente: str | None = Field(None, max_length=100)
    telefono_referente: str | None = Field(None, max_length=30)
    email_referente: EmailStr | None = None

    # Ámbitos de actuación
    ambito_produccion: bool | None = None
    ambito_formacion: bool | None = None
    ambito_exhibicion: bool | None = None
    ambito_comunicacion: bool | None = None
    ambito_distribucion: bool | None = None
    ambito_comunidad: bool | None = None
    ambito_investigacion: bool | None = None
    ambito_otro: bool | None = None
    otro_ambito: str | None = None

    # Objetivos e integrantes
    objetivos: str | None = None
    cantidad_integrantes: int | None = None
    articulo_iaavim: str | None = None
    descripcion_articulacion: str | None = None
    info_adicional_integrantes: str | None = None

    # Documentación
    acta_constitucion_path: str | None = None
    declaracion_objetivos_path: str | None = None

    consentimiento: bool | None = None
    declaracion_inicial: bool | None = None
    borrador: bool | None = None


class AsociacionOut(BaseModel):
    """Schema de salida para Asociación/Colectivo"""

    id: int
    user_id: str

    # Datos básicos y contacto
    nombre_asociacion: str
    anio_creacion: int | None = None
    personeria_juridica: str | None = None
    tipo_personeria: str | None = None
    otra_personeria: str | None = None
    cuit: str | None = None
    domicilio: str
    localidad: str
    distrito: str
    telefono: str | None = None
    email: str
    web: str | None = None

    # Representación
    nombre_referente: str
    rol_referente: str | None = None
    telefono_referente: str | None = None
    email_referente: str | None = None

    # Ámbitos de actuación
    ambito_produccion: bool
    ambito_formacion: bool
    ambito_exhibicion: bool
    ambito_comunicacion: bool
    ambito_distribucion: bool
    ambito_comunidad: bool
    ambito_investigacion: bool
    ambito_otro: bool
    otro_ambito: str | None = None

    # Objetivos e integrantes
    objetivos: str | None = None
    cantidad_integrantes: int | None = None
    articulo_iaavim: str | None = None
    descripcion_articulacion: str | None = None
    info_adicional_integrantes: str | None = None

    # Documentación (paths)
    acta_constitucion_path: str | None = None
    declaracion_objetivos_path: str | None = None

    # Consentimiento
    consentimiento: bool
    declaracion_inicial: bool
    borrador: bool

    # Metadatos
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Integrantes
    integrantes: list[IntegranteAsociacionOut] = []

    model_config = ConfigDict(from_attributes=True)
