from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import date

class RolAtWorkBase(BaseModel):
    nombre: str

class RolAtWorkCreate(RolAtWorkBase):
    pass

class RolAtWork(RolAtWorkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
class TareaAtWorkBase(BaseModel):
    nombre: str

class TareaAtWorkCreate(TareaAtWorkBase):
    pass

class TareaAtWork(TareaAtWorkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TrabajoBase(BaseModel):
    titulo_produccion: str
    tipo_produccion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    descripcion: Optional[str] = None
    enlace_portafolio: Optional[str] = None

class TrabajoCreate(TrabajoBase):
    roles: List[RolAtWorkCreate]
    tareas: List[TareaAtWorkCreate]

class Trabajo(TrabajoBase):
    id: Optional[int] = None
    user_id: str
    roles: List[RolAtWork] = []
    tareas: List[TareaAtWork] = []

    model_config = ConfigDict(from_attributes=True)