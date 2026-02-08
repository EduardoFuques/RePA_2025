# schemas/exhibicion_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# === SALA ===
class SalaCreate(BaseModel):
    """Schema para crear una Sala de Exhibición"""
    nombre: Optional[str] = Field(None, max_length=255)
    tipo_sala: Optional[str] = Field(None, max_length=50)
    otro_tipo: Optional[str] = Field(None, max_length=100)
    
    domicilio: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    
    capacidad: Optional[int] = None
    tiene_proyector_digital: bool = False
    tiene_proyector_35mm: bool = False
    tiene_sonido_dolby: bool = False
    tiene_accesibilidad: bool = False
    otras_caracteristicas: Optional[str] = None
    
    nombre_responsable: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    web: Optional[str] = Field(None, max_length=500)
    borrador: bool = False


class SalaUpdate(BaseModel):
    """Schema para actualizar una Sala"""
    nombre: Optional[str] = Field(None, max_length=255)
    tipo_sala: Optional[str] = Field(None, max_length=50)
    otro_tipo: Optional[str] = Field(None, max_length=100)
    
    domicilio: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    
    capacidad: Optional[int] = None
    tiene_proyector_digital: Optional[bool] = None
    tiene_proyector_35mm: Optional[bool] = None
    tiene_sonido_dolby: Optional[bool] = None
    tiene_accesibilidad: Optional[bool] = None
    otras_caracteristicas: Optional[str] = None
    
    nombre_responsable: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    web: Optional[str] = Field(None, max_length=500)
    activo: Optional[bool] = None
    borrador: Optional[bool] = None


class SalaOut(BaseModel):
    """Schema de salida para Sala"""
    id: int
    user_id: str
    nombre: str
    tipo_sala: str
    otro_tipo: Optional[str] = None
    domicilio: str
    localidad: str
    distrito: str
    capacidad: Optional[int] = None
    tiene_proyector_digital: bool
    tiene_proyector_35mm: bool
    tiene_sonido_dolby: bool
    tiene_accesibilidad: bool
    otras_caracteristicas: Optional[str] = None
    nombre_responsable: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    web: Optional[str] = None
    activo: bool
    borrador: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# === EXHIBICIÓN ===
class ExhibicionCreate(BaseModel):
    """Schema para crear una Exhibición"""
    obra_id: Optional[int] = None
    sala_id: Optional[int] = None
    
    titulo_obra: str = Field(..., min_length=1, max_length=255)
    fecha_exhibicion: date
    cantidad_funciones: int = 1
    
    tipo_exhibicion: str = Field(..., min_length=1, max_length=50)
    nombre_evento: Optional[str] = Field(None, max_length=255)
    
    espectadores_total: Optional[int] = None
    espectadores_pagos: Optional[int] = None
    espectadores_gratuitos: Optional[int] = None
    espectadores_abonados: Optional[int] = None
    
    recaudacion_total: Optional[float] = None
    precio_entrada_general: Optional[float] = None
    
    observaciones: Optional[str] = None
    borrador: bool = False


class ExhibicionUpdate(BaseModel):
    """Schema para actualizar una Exhibición"""
    obra_id: Optional[int] = None
    sala_id: Optional[int] = None
    
    titulo_obra: Optional[str] = Field(None, max_length=255)
    fecha_exhibicion: Optional[date] = None
    cantidad_funciones: Optional[int] = None
    
    tipo_exhibicion: Optional[str] = Field(None, max_length=50)
    nombre_evento: Optional[str] = Field(None, max_length=255)
    
    espectadores_total: Optional[int] = None
    espectadores_pagos: Optional[int] = None
    espectadores_gratuitos: Optional[int] = None
    espectadores_abonados: Optional[int] = None
    
    recaudacion_total: Optional[float] = None
    precio_entrada_general: Optional[float] = None
    
    observaciones: Optional[str] = None
    borrador: Optional[bool] = None


class ExhibicionOut(BaseModel):
    """Schema de salida para Exhibición"""
    id: int
    user_id: str
    obra_id: Optional[int] = None
    sala_id: Optional[int] = None
    titulo_obra: str
    fecha_exhibicion: date
    cantidad_funciones: int
    tipo_exhibicion: str
    nombre_evento: Optional[str] = None
    espectadores_total: Optional[int] = None
    espectadores_pagos: Optional[int] = None
    espectadores_gratuitos: Optional[int] = None
    espectadores_abonados: Optional[int] = None
    recaudacion_total: Optional[float] = None
    precio_entrada_general: Optional[float] = None
    observaciones: Optional[str] = None
    borrador: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# === FESTIVAL ===
class FestivalCreate(BaseModel):
    """Schema para crear un Festival"""
    nombre: str = Field(..., min_length=1, max_length=255)
    edicion: Optional[int] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    
    localidad: str = Field(..., min_length=1, max_length=100)
    distrito: str = Field(..., min_length=1, max_length=50)
    sedes: Optional[List[str]] = None
    
    tipo_festival: Optional[str] = Field(None, max_length=50)
    categorias: Optional[List[str]] = None
    tematica: Optional[str] = Field(None, max_length=255)
    
    cantidad_obras_seleccionadas: Optional[int] = None
    cantidad_obras_misioneras: Optional[int] = None
    cantidad_espectadores: Optional[int] = None
    
    organizador: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    web: Optional[str] = Field(None, max_length=500)
    
    apoyo_iaavim: bool = False
    tipo_apoyo: Optional[str] = Field(None, max_length=255)
    borrador: bool = False


class FestivalUpdate(BaseModel):
    """Schema para actualizar un Festival"""
    nombre: Optional[str] = Field(None, max_length=255)
    edicion: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    
    localidad: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    sedes: Optional[List[str]] = None
    
    tipo_festival: Optional[str] = Field(None, max_length=50)
    categorias: Optional[List[str]] = None
    tematica: Optional[str] = Field(None, max_length=255)
    
    cantidad_obras_seleccionadas: Optional[int] = None
    cantidad_obras_misioneras: Optional[int] = None
    cantidad_espectadores: Optional[int] = None
    
    organizador: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    web: Optional[str] = Field(None, max_length=500)
    
    apoyo_iaavim: Optional[bool] = None
    tipo_apoyo: Optional[str] = Field(None, max_length=255)
    activo: Optional[bool] = None
    borrador: Optional[bool] = None


class FestivalOut(BaseModel):
    """Schema de salida para Festival"""
    id: int
    user_id: str
    nombre: str
    edicion: Optional[int] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    localidad: str
    distrito: str
    sedes: Optional[List[str]] = None
    tipo_festival: Optional[str] = None
    categorias: Optional[List[str]] = None
    tematica: Optional[str] = None
    cantidad_obras_seleccionadas: Optional[int] = None
    cantidad_obras_misioneras: Optional[int] = None
    cantidad_espectadores: Optional[int] = None
    organizador: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    web: Optional[str] = None
    apoyo_iaavim: bool
    tipo_apoyo: Optional[str] = None
    activo: bool
    borrador: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# === CINEMATECA ===
class CinematecaCreate(BaseModel):
    """Schema para crear un registro de Cinemateca"""
    obra_id: int
    
    tipo_soporte: str = Field(..., min_length=1, max_length=50)
    otro_soporte: Optional[str] = Field(None, max_length=100)
    cantidad_copias: int = 1
    
    estado_conservacion: str = Field(..., min_length=1, max_length=30)
    requiere_restauracion: bool = False
    observaciones_estado: Optional[str] = None
    
    ubicacion_fisica: str = Field(..., min_length=1, max_length=255)
    estanteria: Optional[str] = Field(None, max_length=50)
    caja: Optional[str] = Field(None, max_length=50)
    
    digitalizado: bool = False
    formato_digital: Optional[str] = Field(None, max_length=50)
    ubicacion_digital: Optional[str] = Field(None, max_length=500)
    
    disponible_prestamo: bool = True
    fecha_ingreso: Optional[date] = None
    borrador: bool = False


class CinematecaUpdate(BaseModel):
    """Schema para actualizar un registro de Cinemateca"""
    tipo_soporte: Optional[str] = Field(None, max_length=50)
    otro_soporte: Optional[str] = Field(None, max_length=100)
    cantidad_copias: Optional[int] = None
    
    estado_conservacion: Optional[str] = Field(None, max_length=30)
    requiere_restauracion: Optional[bool] = None
    observaciones_estado: Optional[str] = None
    
    ubicacion_fisica: Optional[str] = Field(None, max_length=255)
    estanteria: Optional[str] = Field(None, max_length=50)
    caja: Optional[str] = Field(None, max_length=50)
    
    digitalizado: Optional[bool] = None
    formato_digital: Optional[str] = Field(None, max_length=50)
    ubicacion_digital: Optional[str] = Field(None, max_length=500)
    
    disponible_prestamo: Optional[bool] = None
    en_prestamo: Optional[bool] = None
    borrador: Optional[bool] = None


class CinematecaOut(BaseModel):
    """Schema de salida para Cinemateca"""
    id: int
    obra_id: int
    tipo_soporte: str
    otro_soporte: Optional[str] = None
    cantidad_copias: int
    estado_conservacion: str
    requiere_restauracion: bool
    observaciones_estado: Optional[str] = None
    ubicacion_fisica: str
    estanteria: Optional[str] = None
    caja: Optional[str] = None
    digitalizado: bool
    formato_digital: Optional[str] = None
    ubicacion_digital: Optional[str] = None
    disponible_prestamo: bool
    en_prestamo: bool
    fecha_ultimo_prestamo: Optional[date] = None
    fecha_ingreso: Optional[date] = None
    borrador: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
