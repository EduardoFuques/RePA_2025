# schemas/obra_audiovisual_schemas.py

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# === EQUIPO TÉCNICO ===
class EquipoTecnicoBase(BaseModel):
    rol: str | None = Field(None, max_length=100)
    nombre: str | None = Field(None, max_length=200)
    en_repa: str | None = None
    codigo_repa: str | None = None


class EquipoTecnicoCreate(EquipoTecnicoBase):
    pass


class EquipoTecnicoOut(EquipoTecnicoBase):
    id: int
    obra_id: int

    model_config = ConfigDict(from_attributes=True)


# === SCHEMA PRINCIPAL ===
class ObraAudiovisualCreate(BaseModel):
    """Schema para crear una Obra Audiovisual (AGAM)"""

    # Identificación
    titulo: str | None = Field(None, max_length=255)
    anio_estreno: int | None = None
    anio_ingreso: int | None = None
    duracion_minutos: int | None = None
    tipo_produccion: str | None = None
    extension: str | None = None
    formato_narrativo: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    medio: str | None = None

    # Datos técnicos
    formatos_disponibles: list[str] | None = None
    otro_formato: str | None = None
    resolucion: str | None = None
    idioma_original: str | None = None
    subtitulos: str | None = None
    uso_material: list[str] | None = None
    otro_uso: str | None = None
    ubicacion: str | None = None

    # Datos relacionales
    productora_responsable: str | None = None
    codigo_repa_productora: str | None = None
    participo_fomento: str | None = None
    lineas_fomento: list[str] | None = None
    otro_fomento: str | None = None
    registro_obra_nacional: str | None = None
    vinculos_areas: list[str] | None = None

    # Derechos
    autoriza_exhibicion: str | None = None
    autoriza_investigacion: str | None = None
    convenio_cesion: str | None = None
    restricciones: str | None = None

    # Equipo técnico (opcional en creación, se puede agregar después)
    equipo_tecnico: list[EquipoTecnicoCreate] | None = None

    # Estado
    borrador: bool = True


class ObraAudiovisualUpdate(BaseModel):
    """Schema para actualizar una Obra Audiovisual"""

    # Identificación
    titulo: str | None = Field(None, max_length=255)
    anio_estreno: int | None = None
    anio_ingreso: int | None = None
    duracion_minutos: int | None = None
    tipo_produccion: str | None = None
    extension: str | None = None
    formato_narrativo: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    medio: str | None = None

    # Datos técnicos
    formatos_disponibles: list[str] | None = None
    otro_formato: str | None = None
    resolucion: str | None = None
    idioma_original: str | None = None
    subtitulos: str | None = None
    uso_material: list[str] | None = None
    otro_uso: str | None = None
    ubicacion: str | None = None

    # Datos relacionales
    productora_responsable: str | None = None
    codigo_repa_productora: str | None = None
    participo_fomento: str | None = None
    lineas_fomento: list[str] | None = None
    otro_fomento: str | None = None
    registro_obra_nacional: str | None = None
    vinculos_areas: list[str] | None = None

    # Derechos
    autoriza_exhibicion: str | None = None
    autoriza_investigacion: str | None = None
    convenio_cesion: str | None = None
    restricciones: str | None = None

    # Estado
    borrador: bool | None = None


class ObraAudiovisualOut(BaseModel):
    """Schema de salida para Obra Audiovisual"""

    id: int
    user_id: str
    codigo_agam: str | None = None

    # Identificación
    titulo: str
    anio_estreno: int | None = None
    anio_ingreso: int | None = None
    duracion_minutos: int | None = None
    tipo_produccion: str | None = None
    extension: str | None = None
    formato_narrativo: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    medio: str | None = None

    # Datos técnicos
    formatos_disponibles: list[str] | None = None
    otro_formato: str | None = None
    resolucion: str | None = None
    idioma_original: str | None = None
    subtitulos: str | None = None
    uso_material: list[str] | None = None
    otro_uso: str | None = None
    ficha_tecnica_path: str | None = None
    ubicacion: str | None = None

    # Datos relacionales
    productora_responsable: str | None = None
    codigo_repa_productora: str | None = None
    participo_fomento: str | None = None
    lineas_fomento: list[str] | None = None
    otro_fomento: str | None = None
    registro_obra_nacional: str | None = None
    vinculos_areas: list[str] | None = None

    # Derechos
    autoriza_exhibicion: str | None = None
    autoriza_investigacion: str | None = None
    convenio_cesion: str | None = None
    archivo_convenio_path: str | None = None
    restricciones: str | None = None

    # Equipo técnico
    equipo_tecnico: list[EquipoTecnicoOut] = []

    # Estado
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ObraAudiovisualList(BaseModel):
    """Schema resumido para listados de obras"""

    id: int
    codigo_agam: str | None = None
    titulo: str
    anio_estreno: int | None = None
    genero: str | None = None
    extension: str | None = None

    model_config = ConfigDict(from_attributes=True)
