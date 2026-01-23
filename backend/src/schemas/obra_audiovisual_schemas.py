# schemas/obra_audiovisual_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# === EQUIPO TÉCNICO ===
class EquipoTecnicoBase(BaseModel):
    rol: str = Field(..., min_length=1, max_length=100)
    nombre: str = Field(..., min_length=1, max_length=200)
    en_repa: Optional[str] = None
    codigo_repa: Optional[str] = None

class EquipoTecnicoCreate(EquipoTecnicoBase):
    pass

class EquipoTecnicoOut(EquipoTecnicoBase):
    id: int
    obra_id: int
    
    class Config:
        from_attributes = True

# === SCHEMA PRINCIPAL ===
class ObraAudiovisualCreate(BaseModel):
    """Schema para crear una Obra Audiovisual (AGAM)"""
    
    # Identificación
    titulo: str = Field(..., min_length=1, max_length=255)
    anio_estreno: Optional[int] = None
    anio_ingreso: Optional[int] = None
    duracion_minutos: Optional[int] = None
    tipo_produccion: Optional[str] = None
    extension: Optional[str] = None
    formato_narrativo: Optional[str] = None
    genero: Optional[str] = None
    subgenero: Optional[str] = None
    medio: Optional[str] = None
    
    # Datos técnicos
    formatos_disponibles: Optional[List[str]] = None
    otro_formato: Optional[str] = None
    resolucion: Optional[str] = None
    idioma_original: Optional[str] = None
    subtitulos: Optional[str] = None
    uso_material: Optional[List[str]] = None
    otro_uso: Optional[str] = None
    ubicacion: Optional[str] = None
    
    # Datos relacionales
    productora_responsable: Optional[str] = None
    codigo_repa_productora: Optional[str] = None
    participo_fomento: Optional[str] = None
    lineas_fomento: Optional[List[str]] = None
    otro_fomento: Optional[str] = None
    registro_obra_nacional: Optional[str] = None
    vinculos_areas: Optional[List[str]] = None
    
    # Derechos
    autoriza_exhibicion: Optional[str] = None
    autoriza_investigacion: Optional[str] = None
    convenio_cesion: Optional[str] = None
    restricciones: Optional[str] = None
    
    # Equipo técnico (opcional en creación, se puede agregar después)
    equipo_tecnico: Optional[List[EquipoTecnicoCreate]] = None


class ObraAudiovisualUpdate(BaseModel):
    """Schema para actualizar una Obra Audiovisual"""
    
    # Identificación
    titulo: Optional[str] = Field(None, max_length=255)
    anio_estreno: Optional[int] = None
    anio_ingreso: Optional[int] = None
    duracion_minutos: Optional[int] = None
    tipo_produccion: Optional[str] = None
    extension: Optional[str] = None
    formato_narrativo: Optional[str] = None
    genero: Optional[str] = None
    subgenero: Optional[str] = None
    medio: Optional[str] = None
    
    # Datos técnicos
    formatos_disponibles: Optional[List[str]] = None
    otro_formato: Optional[str] = None
    resolucion: Optional[str] = None
    idioma_original: Optional[str] = None
    subtitulos: Optional[str] = None
    uso_material: Optional[List[str]] = None
    otro_uso: Optional[str] = None
    ubicacion: Optional[str] = None
    
    # Datos relacionales
    productora_responsable: Optional[str] = None
    codigo_repa_productora: Optional[str] = None
    participo_fomento: Optional[str] = None
    lineas_fomento: Optional[List[str]] = None
    otro_fomento: Optional[str] = None
    registro_obra_nacional: Optional[str] = None
    vinculos_areas: Optional[List[str]] = None
    
    # Derechos
    autoriza_exhibicion: Optional[str] = None
    autoriza_investigacion: Optional[str] = None
    convenio_cesion: Optional[str] = None
    restricciones: Optional[str] = None


class ObraAudiovisualOut(BaseModel):
    """Schema de salida para Obra Audiovisual"""
    id: int
    user_id: str
    codigo_agam: Optional[str] = None
    
    # Identificación
    titulo: str
    anio_estreno: Optional[int] = None
    anio_ingreso: Optional[int] = None
    duracion_minutos: Optional[int] = None
    tipo_produccion: Optional[str] = None
    extension: Optional[str] = None
    formato_narrativo: Optional[str] = None
    genero: Optional[str] = None
    subgenero: Optional[str] = None
    medio: Optional[str] = None
    
    # Datos técnicos
    formatos_disponibles: Optional[List[str]] = None
    otro_formato: Optional[str] = None
    resolucion: Optional[str] = None
    idioma_original: Optional[str] = None
    subtitulos: Optional[str] = None
    uso_material: Optional[List[str]] = None
    otro_uso: Optional[str] = None
    ficha_tecnica_path: Optional[str] = None
    ubicacion: Optional[str] = None
    
    # Datos relacionales
    productora_responsable: Optional[str] = None
    codigo_repa_productora: Optional[str] = None
    participo_fomento: Optional[str] = None
    lineas_fomento: Optional[List[str]] = None
    otro_fomento: Optional[str] = None
    registro_obra_nacional: Optional[str] = None
    vinculos_areas: Optional[List[str]] = None
    
    # Derechos
    autoriza_exhibicion: Optional[str] = None
    autoriza_investigacion: Optional[str] = None
    convenio_cesion: Optional[str] = None
    archivo_convenio_path: Optional[str] = None
    restricciones: Optional[str] = None
    
    # Equipo técnico
    equipo_tecnico: List[EquipoTecnicoOut] = []
    
    class Config:
        from_attributes = True


class ObraAudiovisualList(BaseModel):
    """Schema resumido para listados de obras"""
    id: int
    codigo_agam: Optional[str] = None
    titulo: str
    anio_estreno: Optional[int] = None
    genero: Optional[str] = None
    extension: Optional[str] = None
    
    class Config:
        from_attributes = True
