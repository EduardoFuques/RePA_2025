# schemas/exhibicion_schemas.py
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# === SALA ===
class SalaCreate(BaseModel):
    """Schema para crear una Sala de Exhibición"""

    nombre: str | None = Field(None, max_length=255)
    tipo_sala: str | None = Field(None, max_length=50)
    otro_tipo: str | None = Field(None, max_length=100)

    domicilio: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)

    capacidad: int | None = None
    tiene_proyector_digital: bool = False
    tiene_proyector_35mm: bool = False
    tiene_sonido_dolby: bool = False
    tiene_accesibilidad: bool = False
    otras_caracteristicas: str | None = None

    nombre_responsable: str | None = Field(None, max_length=200)
    telefono: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    web: str | None = Field(None, max_length=500)

    responsable_legal: dict | None = None
    programador: dict | None = None
    responsable_tecnico: dict | None = None
    afiliaciones: dict | None = None
    consentimiento: bool = False
    borrador: bool = False


class SalaUpdate(BaseModel):
    """Schema para actualizar una Sala"""

    nombre: str | None = Field(None, max_length=255)
    tipo_sala: str | None = Field(None, max_length=50)
    otro_tipo: str | None = Field(None, max_length=100)

    domicilio: str | None = Field(None, max_length=255)
    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)

    capacidad: int | None = None
    tiene_proyector_digital: bool | None = None
    tiene_proyector_35mm: bool | None = None
    tiene_sonido_dolby: bool | None = None
    tiene_accesibilidad: bool | None = None
    otras_caracteristicas: str | None = None

    nombre_responsable: str | None = Field(None, max_length=200)
    telefono: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    web: str | None = Field(None, max_length=500)

    responsable_legal: dict | None = None
    programador: dict | None = None
    responsable_tecnico: dict | None = None
    afiliaciones: dict | None = None
    consentimiento: bool | None = None
    activo: bool | None = None
    borrador: bool | None = None


class SalaOut(BaseModel):
    """Schema de salida para Sala"""

    id: int
    user_id: str
    nombre: str | None = None
    tipo_sala: str | None = None
    otro_tipo: str | None = None
    domicilio: str | None = None
    localidad: str | None = None
    distrito: str | None = None
    capacidad: int | None = None
    tiene_proyector_digital: bool
    tiene_proyector_35mm: bool
    tiene_sonido_dolby: bool
    tiene_accesibilidad: bool
    otras_caracteristicas: str | None = None
    nombre_responsable: str | None = None
    telefono: str | None = None
    email: str | None = None
    web: str | None = None
    responsable_legal: dict | None = None
    programador: dict | None = None
    responsable_tecnico: dict | None = None
    afiliaciones: dict | None = None
    consentimiento: bool = False
    activo: bool
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === EXHIBICIÓN ===
class ExhibicionCreate(BaseModel):
    """Schema para crear una Exhibición"""

    obra_id: int | None = None
    sala_id: int | None = None

    titulo_obra: str | None = Field(None, max_length=255)
    fecha_exhibicion: date | None = None
    cantidad_funciones: int = 1

    tipo_exhibicion: str | None = Field(None, max_length=50)
    nombre_evento: str | None = Field(None, max_length=255)

    espectadores_total: int | None = None
    espectadores_pagos: int | None = None
    espectadores_gratuitos: int | None = None
    espectadores_abonados: int | None = None

    recaudacion_total: float | None = None
    precio_entrada_general: float | None = None

    observaciones: str | None = None
    borrador: bool = False


class ExhibicionUpdate(BaseModel):
    """Schema para actualizar una Exhibición"""

    obra_id: int | None = None
    sala_id: int | None = None

    titulo_obra: str | None = Field(None, max_length=255)
    fecha_exhibicion: date | None = None
    cantidad_funciones: int | None = None

    tipo_exhibicion: str | None = Field(None, max_length=50)
    nombre_evento: str | None = Field(None, max_length=255)

    espectadores_total: int | None = None
    espectadores_pagos: int | None = None
    espectadores_gratuitos: int | None = None
    espectadores_abonados: int | None = None

    recaudacion_total: float | None = None
    precio_entrada_general: float | None = None

    observaciones: str | None = None
    borrador: bool | None = None


class ExhibicionOut(BaseModel):
    """Schema de salida para Exhibición"""

    id: int
    user_id: str
    obra_id: int | None = None
    sala_id: int | None = None
    titulo_obra: str | None = None
    fecha_exhibicion: date | None = None
    cantidad_funciones: int = 1
    tipo_exhibicion: str | None = None
    nombre_evento: str | None = None
    espectadores_total: int | None = None
    espectadores_pagos: int | None = None
    espectadores_gratuitos: int | None = None
    espectadores_abonados: int | None = None
    recaudacion_total: float | None = None
    precio_entrada_general: float | None = None
    observaciones: str | None = None
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === FESTIVAL ===
class FestivalCreate(BaseModel):
    """Schema para crear un Festival"""

    nombre: str | None = Field(None, max_length=255)
    edicion: int | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    sedes: list[str] | None = None

    tipo_festival: str | None = Field(None, max_length=50)
    categorias: list[str] | None = None
    tematica: str | None = Field(None, max_length=255)

    cantidad_obras_seleccionadas: int | None = None
    cantidad_obras_misioneras: int | None = None
    cantidad_espectadores: int | None = None

    organizador: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    web: str | None = Field(None, max_length=500)

    periodicidad: str | None = Field(None, max_length=50)
    anio_inicio: int | None = None
    responsable: dict | None = None
    curaduria: bool = False
    calendario_oficial: bool = False

    apoyo_iaavim: bool = False
    tipo_apoyo: str | None = Field(None, max_length=255)
    consentimiento: bool = False
    desea_recibir_info: bool = False
    borrador: bool = False


class FestivalUpdate(BaseModel):
    """Schema para actualizar un Festival"""

    nombre: str | None = Field(None, max_length=255)
    edicion: int | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

    localidad: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)
    sedes: list[str] | None = None

    tipo_festival: str | None = Field(None, max_length=50)
    categorias: list[str] | None = None
    tematica: str | None = Field(None, max_length=255)

    cantidad_obras_seleccionadas: int | None = None
    cantidad_obras_misioneras: int | None = None
    cantidad_espectadores: int | None = None

    organizador: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    web: str | None = Field(None, max_length=500)

    periodicidad: str | None = Field(None, max_length=50)
    anio_inicio: int | None = None
    responsable: dict | None = None
    curaduria: bool | None = None
    calendario_oficial: bool | None = None

    apoyo_iaavim: bool | None = None
    tipo_apoyo: str | None = Field(None, max_length=255)
    consentimiento: bool | None = None
    desea_recibir_info: bool | None = None
    activo: bool | None = None
    borrador: bool | None = None


class FestivalOut(BaseModel):
    """Schema de salida para Festival"""

    id: int
    user_id: str
    nombre: str | None = None
    edicion: int | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    localidad: str | None = None
    distrito: str | None = None
    sedes: list[str] | None = None
    tipo_festival: str | None = None
    categorias: list[str] | None = None
    tematica: str | None = None
    cantidad_obras_seleccionadas: int | None = None
    cantidad_obras_misioneras: int | None = None
    cantidad_espectadores: int | None = None
    organizador: str | None = None
    email: str | None = None
    telefono: str | None = None
    web: str | None = None
    periodicidad: str | None = None
    anio_inicio: int | None = None
    responsable: dict | None = None
    curaduria: bool = False
    calendario_oficial: bool = False
    apoyo_iaavim: bool
    tipo_apoyo: str | None = None
    consentimiento: bool = False
    desea_recibir_info: bool = False
    activo: bool
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === CINEMATECA ===
class CinematecaCreate(BaseModel):
    """Schema para crear un registro de Cinemateca"""

    obra_id: int | None = None

    tipo_soporte: str | None = Field(None, max_length=50)
    otro_soporte: str | None = Field(None, max_length=100)
    cantidad_copias: int = 1

    estado_conservacion: str | None = Field(None, max_length=30)
    requiere_restauracion: bool = False
    observaciones_estado: str | None = None

    ubicacion_fisica: str | None = Field(None, max_length=255)
    estanteria: str | None = Field(None, max_length=50)
    caja: str | None = Field(None, max_length=50)

    digitalizado: bool = False
    formato_digital: str | None = Field(None, max_length=50)
    ubicacion_digital: str | None = Field(None, max_length=500)

    disponible_prestamo: bool = True
    fecha_ingreso: date | None = None
    borrador: bool = False


class CinematecaUpdate(BaseModel):
    """Schema para actualizar un registro de Cinemateca"""

    tipo_soporte: str | None = Field(None, max_length=50)
    otro_soporte: str | None = Field(None, max_length=100)
    cantidad_copias: int | None = None

    estado_conservacion: str | None = Field(None, max_length=30)
    requiere_restauracion: bool | None = None
    observaciones_estado: str | None = None

    ubicacion_fisica: str | None = Field(None, max_length=255)
    estanteria: str | None = Field(None, max_length=50)
    caja: str | None = Field(None, max_length=50)

    digitalizado: bool | None = None
    formato_digital: str | None = Field(None, max_length=50)
    ubicacion_digital: str | None = Field(None, max_length=500)

    disponible_prestamo: bool | None = None
    en_prestamo: bool | None = None
    borrador: bool | None = None


class CinematecaOut(BaseModel):
    """Schema de salida para Cinemateca"""

    id: int
    obra_id: int | None = None
    tipo_soporte: str | None = None
    otro_soporte: str | None = None
    cantidad_copias: int = 1
    estado_conservacion: str | None = None
    requiere_restauracion: bool = False
    observaciones_estado: str | None = None
    ubicacion_fisica: str | None = None
    estanteria: str | None = None
    caja: str | None = None
    digitalizado: bool
    formato_digital: str | None = None
    ubicacion_digital: str | None = None
    disponible_prestamo: bool
    en_prestamo: bool
    fecha_ultimo_prestamo: date | None = None
    fecha_ingreso: date | None = None
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
