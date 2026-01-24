from pydantic import BaseModel, field_validator, HttpUrl, Field, ConfigDict
from typing import Optional
from datetime import date

class TrainingBase(BaseModel):
    nombre_curso: str = Field("nombre_curso", min_length=1, max_length=255)
    institucion: str = Field("institucion", max_length=255)
    tipo_certificado: str = Field("tipo_certificado", max_length=100)
    nivel_estudio: str = Field("nivel_estudio", max_length=100)
    fecha_inicio: date
    fecha_finalizacion: date
    horas_duracion: float
    enlace_certificado: str = Field("enlace_certificado", max_length=250)  # Validación de URL automática
    area_conocimiento: str = Field("area_conocimiento", max_length=100)
    descripcion_curso: str = Field("descripcion_curso", max_length=1500)
    calificacion_nota: str = Field("calificacion_nota", max_length=50)
    idioma: str = Field("idioma", max_length=50)
    nombre_profesor_instructor: str = Field("nombre_profesor_instructor", max_length=255)
    nombre_programa_estudios: str = Field("nombre_programa_estudios", max_length=255)
    pais: str = Field("pais", max_length=100)
    ciudad: str = Field("ciudad", max_length=100)
    estado_provincia: str = Field("estado_provincia", max_length=100)
    observaciones: str = Field("observaciones", max_length=1000)

    @field_validator('fecha_finalizacion')
    def validate_fechas(cls, fecha_finalizacion: date, values):
        fecha_inicio = values.data.get('fecha_inicio')
        
        if fecha_inicio and fecha_finalizacion <= fecha_inicio:
            raise ValueError(
                "La fecha de finalización debe ser posterior a la fecha de inicio"
            )
        return fecha_finalizacion

    @field_validator('horas_duracion')
    def validate_horas(cls, horas: float):
        if horas <= 0:
            raise ValueError(
                "Las horas de duración deben ser un valor positivo mayor a cero"
            )
        return horas
    
    @field_validator('idioma')
    def validate_idioma(cls, idioma: str):
        if len(idioma) != 2 or not idioma.isalpha():
            raise ValueError("El idioma debe ser un código ISO 639-1 de 2 letras")
        return idioma.lower()
    
class TrainingCreate(TrainingBase):
    pass

class TrainingUpdate(TrainingBase):
    pass

class TrainingOut(TrainingBase):
    id: int
    user_id: str
    
    model_config = ConfigDict(from_attributes=True)

