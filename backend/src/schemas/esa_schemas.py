# schemas/esa_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

class EstudianteESACreate(BaseModel):
    """Schema para crear un registro de Estudiante ESA"""
    
    # Datos personales - permitidos null para borradores
    nombre_completo: Optional[str] = Field(None, max_length=200)
    dni: Optional[str] = Field(None, max_length=20)
    cuil: Optional[str] = Field(None, max_length=15)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    
    # Localización
    municipio: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=20)
    
    # Formación
    institucion: Optional[str] = Field(None, max_length=255)
    otra_institucion: Optional[str] = Field(None, max_length=255)
    carrera: Optional[str] = Field(None, max_length=255)
    anio_cursado: Optional[int] = None
    modalidad: Optional[str] = Field(None, max_length=20)
    
    # Intereses
    areas_interes: Optional[List[str]] = None
    otra_area: Optional[str] = None
    participo_proyecto: Optional[bool] = None
    descripcion_experiencia: Optional[str] = None
    
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
    nombre_completo: Optional[str] = Field(None, max_length=200)
    dni: Optional[str] = Field(None, max_length=20)
    cuil: Optional[str] = Field(None, max_length=15)
    fecha_nacimiento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    genero: Optional[str] = Field(None, max_length=50)
    
    # Localización
    municipio: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=20)
    
    # Formación
    institucion: Optional[str] = Field(None, max_length=255)
    otra_institucion: Optional[str] = Field(None, max_length=255)
    carrera: Optional[str] = Field(None, max_length=255)
    anio_cursado: Optional[int] = None
    modalidad: Optional[str] = Field(None, max_length=20)
    
    # Intereses
    areas_interes: Optional[List[str]] = None
    otra_area: Optional[str] = None
    participo_proyecto: Optional[bool] = None
    descripcion_experiencia: Optional[str] = None
    
    # Declaraciones
    estudiante_activo: Optional[bool] = None
    leyo_reglamento: Optional[bool] = None
    no_inscripto_repa: Optional[bool] = None
    vigencia_un_anio: Optional[bool] = None
    autoriza_datos: Optional[bool] = None
    borrador: Optional[bool] = None


class EstudianteESAOut(BaseModel):
    """Schema de salida para Estudiante ESA"""
    id: int
    user_id: str
    
    # Datos personales
    nombre_completo: str
    dni: str
    cuil: str
    fecha_nacimiento: date
    genero: Optional[str] = None
    email: str
    telefono: str
    
    # Localización
    municipio: str
    distrito: str
    
    # Formación
    institucion: str
    otra_institucion: Optional[str] = None
    carrera: str
    anio_cursado: Optional[int] = None
    modalidad: str
    
    # Intereses
    areas_interes: Optional[List[str]] = None
    otra_area: Optional[str] = None
    participo_proyecto: Optional[bool] = None
    descripcion_experiencia: Optional[str] = None
    
    # Declaraciones
    estudiante_activo: bool
    leyo_reglamento: bool
    no_inscripto_repa: bool
    vigencia_un_anio: bool
    autoriza_datos: bool
    borrador: bool
    
    # Metadatos
    fecha_alta: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
