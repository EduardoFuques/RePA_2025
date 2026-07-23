# schemas/esa_schemas.py
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.lifecycle_schemas import RegistroLifecycleOut


class EstudianteESACreate(BaseModel):
    """Schema para crear un registro de Estudiante ESA"""

    # Datos personales - permitidos null para borradores
    nombre_completo: str | None = Field(None, max_length=200)
    dni: str | None = Field(None, max_length=20)
    cuil: str | None = Field(None, max_length=15)
    fecha_nacimiento: date | None = None
    genero: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)

    # Localización
    municipio: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=20)

    # Formación
    institucion: str | None = Field(None, max_length=255)
    otra_institucion: str | None = Field(None, max_length=255)
    carrera: str | None = Field(None, max_length=255)
    anio_cursado: int | None = None
    modalidad: str | None = Field(None, max_length=20)

    # Intereses
    areas_interes: list[str] | None = None
    otra_area: str | None = None
    participo_proyecto: bool | None = None
    descripcion_experiencia: str | None = None

    # Documentación adjunta
    certificado_alumno_path: str | None = Field(None, max_length=500)
    copia_dni_path: str | None = Field(None, max_length=500)

    # Declaraciones
    estudiante_activo: bool = False
    leyo_reglamento: bool = False
    no_inscripto_repa: bool = False
    vigencia_un_anio: bool = False
    autoriza_datos: bool = False
    borrador: bool = False


class EstudianteESAUpdate(BaseModel):
    """Schema para actualizar un registro de Estudiante ESA"""

    # Datos personales
    nombre_completo: str | None = Field(None, max_length=200)
    dni: str | None = Field(None, max_length=20)
    cuil: str | None = Field(None, max_length=15)
    fecha_nacimiento: date | None = None
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    genero: str | None = Field(None, max_length=50)

    # Localización
    municipio: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=20)

    # Formación
    institucion: str | None = Field(None, max_length=255)
    otra_institucion: str | None = Field(None, max_length=255)
    carrera: str | None = Field(None, max_length=255)
    anio_cursado: int | None = None
    modalidad: str | None = Field(None, max_length=20)

    # Intereses
    areas_interes: list[str] | None = None
    otra_area: str | None = None
    participo_proyecto: bool | None = None
    descripcion_experiencia: str | None = None

    # Documentación adjunta
    certificado_alumno_path: str | None = Field(None, max_length=500)
    copia_dni_path: str | None = Field(None, max_length=500)

    # Declaraciones
    estudiante_activo: bool | None = None
    leyo_reglamento: bool | None = None
    no_inscripto_repa: bool | None = None
    vigencia_un_anio: bool | None = None
    autoriza_datos: bool | None = None
    borrador: bool | None = None


class EstudianteESAOut(RegistroLifecycleOut):
    """Schema de salida para Estudiante ESA"""

    id: int
    user_id: str

    # Datos personales
    nombre_completo: str | None = None
    dni: str | None = None
    cuil: str | None = None
    fecha_nacimiento: date | None = None
    genero: str | None = None
    email: str | None = None
    telefono: str | None = None

    # Localización
    municipio: str | None = None
    distrito: str | None = None

    # Formación
    institucion: str | None = None
    otra_institucion: str | None = None
    carrera: str | None = None
    anio_cursado: int | None = None
    modalidad: str | None = None

    # Intereses
    areas_interes: list[str] | None = None
    otra_area: str | None = None
    participo_proyecto: bool | None = None
    descripcion_experiencia: str | None = None

    # Documentación adjunta
    certificado_alumno_path: str | None = None
    copia_dni_path: str | None = None

    # Declaraciones
    estudiante_activo: bool
    leyo_reglamento: bool
    no_inscripto_repa: bool
    vigencia_un_anio: bool
    autoriza_datos: bool
    borrador: bool

    # Metadatos
    fecha_alta: datetime | None = None
    fecha_vencimiento: datetime | None = None
    activo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
