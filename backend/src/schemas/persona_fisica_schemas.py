# schemas/persona_fisica_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# === DATOS PERSONALES ===
class DatosPersonalesBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    dni: str = Field(..., min_length=1, max_length=20)
    cuil: str = Field(..., min_length=1, max_length=15)
    fecha_nacimiento: date
    email: EmailStr
    telefono: str = Field(..., min_length=1, max_length=30)
    domicilio: str = Field(..., min_length=1, max_length=255)
    municipio: str = Field(..., min_length=1, max_length=100)
    distrito: str = Field(..., min_length=1, max_length=50)

# === EDUCACIÓN ===
class EducacionBase(BaseModel):
    nivel_educativo: Optional[str] = None
    trabajo_final: Optional[bool] = None
    titulo_tesis: Optional[str] = None

# === IDENTIDADES ===
class IdentidadesBase(BaseModel):
    pueblo_originario: Optional[str] = None  # si, no, prefiere_no_responder
    cual_pueblo: Optional[str] = None
    afrodescendiente: Optional[str] = None  # si, no, prefiere_no_responder
    lgbtiq: Optional[str] = None  # si, no, prefiere_no_responder
    discapacidad: Optional[str] = None  # si, no, prefiere_no_responder
    tipo_discapacidad: Optional[str] = None
    personas_a_cargo: Optional[bool] = None
    tipo_personas_a_cargo: Optional[List[str]] = None
    otros_personas_a_cargo: Optional[str] = None

# === LABORAL ===
class LaboralBase(BaseModel):
    principal_fuente_audiovisual: Optional[bool] = None
    otra_fuente: Optional[str] = None
    relacion_laboral: Optional[str] = None
    otra_relacion: Optional[str] = None
    inscripto_afip: Optional[str] = None
    situacion_iva: Optional[str] = None
    pertenece_red: Optional[bool] = None
    nombre_red: Optional[str] = None

# === INTERÉS INSTITUCIONAL ===
class InteresBase(BaseModel):
    proyectos_iaavim: Optional[bool] = None
    conoce_lineas_fomento: Optional[str] = None  # si, no, parcialmente
    interes_formacion: Optional[bool] = None
    areas_capacitacion: Optional[str] = None
    interes_difusion: Optional[bool] = None
    interes_experto_iaavim: Optional[bool] = None

# === SUBPERFILES ===
class ObraSubperfilBase(BaseModel):
    titulo_obra: str = Field(..., min_length=1, max_length=255)
    anio: Optional[int] = None
    rol: Optional[str] = None

class TecnicoArtisticoBase(BaseModel):
    areas: Optional[List[str]] = None
    medios: Optional[List[str]] = None
    obras_iaavim: Optional[List[str]] = None
    especializaciones: Optional[List[str]] = None

class CapacitadorBase(BaseModel):
    capacitaciones_iaavim: bool = False
    capacitaciones: Optional[List[dict]] = None
    capacitador_actual: bool = False
    areas_capacitacion: Optional[str] = None
    publico_destinatario: Optional[str] = None
    tipos_instituciones: Optional[List[str]] = None
    disena_contenidos: bool = False
    interes_lista_expertos: bool = False
    cv_link: Optional[str] = None
    materiales_link: Optional[str] = None

class InvestigadorBase(BaseModel):
    participo_proyectos: bool = False
    proyectos: Optional[List[dict]] = None
    tiene_publicaciones: bool = False
    publicaciones_link: Optional[str] = None
    tematica_principal: Optional[str] = None
    enfoque: Optional[str] = None
    pertenece_grupo: bool = False
    nombre_grupo: Optional[str] = None
    recibio_financiamiento: bool = False
    institucion_financiamiento: Optional[str] = None
    interes_red_investigadores: bool = False

# === CONSENTIMIENTO ===
class ConsentimientoBase(BaseModel):
    acepta_terminos: bool = False
    portfolio_link: Optional[str] = None

# === SCHEMA PRINCIPAL ===
class PersonaFisicaCreate(BaseModel):
    """Schema para crear una Persona Física"""
    declaracion_inicial: bool = True
    
    # Datos personales - permitidos null para borradores
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    dni: Optional[str] = Field(None, max_length=20)
    cuil: Optional[str] = Field(None, max_length=15)
    fecha_nacimiento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    domicilio: Optional[str] = Field(None, max_length=255)
    municipio: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    
    # Educación
    nivel_educativo: Optional[str] = None
    trabajo_final: Optional[bool] = None
    titulo_tesis: Optional[str] = None
    
    # Identidades
    pueblo_originario: Optional[str] = None
    cual_pueblo: Optional[str] = None
    afrodescendiente: Optional[str] = None
    lgbtiq: Optional[str] = None
    discapacidad: Optional[str] = None
    tipo_discapacidad: Optional[str] = None
    personas_a_cargo: Optional[bool] = None
    tipo_personas_a_cargo: Optional[List[str]] = None
    otros_personas_a_cargo: Optional[str] = None
    
    # Laboral
    principal_fuente_audiovisual: Optional[bool] = None
    otra_fuente: Optional[str] = None
    relacion_laboral: Optional[str] = None
    otra_relacion: Optional[str] = None
    inscripto_afip: Optional[str] = None
    situacion_iva: Optional[str] = None
    pertenece_red: Optional[bool] = None
    nombre_red: Optional[str] = None
    
    # Interés institucional
    proyectos_iaavim: Optional[bool] = None
    conoce_lineas_fomento: Optional[str] = None
    interes_formacion: Optional[bool] = None
    areas_capacitacion: Optional[str] = None
    interes_difusion: Optional[bool] = None
    interes_experto_iaavim: Optional[bool] = None
    
    # Subperfiles
    subperfiles_seleccionados: Optional[List[str]] = None
    
    # Consentimiento
    acepta_terminos: bool = False
    portfolio_link: Optional[str] = None
    dni_adjunto_path: Optional[str] = None
    borrador: bool = False


class PersonaFisicaUpdate(BaseModel):
    """Schema para actualizar una Persona Física"""
    # Datos personales
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=30)
    domicilio: Optional[str] = Field(None, max_length=255)
    municipio: Optional[str] = Field(None, max_length=100)
    distrito: Optional[str] = Field(None, max_length=50)
    
    # Educación
    nivel_educativo: Optional[str] = None
    trabajo_final: Optional[bool] = None
    titulo_tesis: Optional[str] = None
    
    # Identidades
    pueblo_originario: Optional[str] = None
    cual_pueblo: Optional[str] = None
    afrodescendiente: Optional[str] = None
    lgbtiq: Optional[str] = None
    discapacidad: Optional[str] = None
    tipo_discapacidad: Optional[str] = None
    personas_a_cargo: Optional[bool] = None
    tipo_personas_a_cargo: Optional[List[str]] = None
    otros_personas_a_cargo: Optional[str] = None
    
    # Laboral
    principal_fuente_audiovisual: Optional[bool] = None
    otra_fuente: Optional[str] = None
    relacion_laboral: Optional[str] = None
    otra_relacion: Optional[str] = None
    inscripto_afip: Optional[str] = None
    situacion_iva: Optional[str] = None
    pertenece_red: Optional[bool] = None
    nombre_red: Optional[str] = None
    
    # Interés institucional
    proyectos_iaavim: Optional[bool] = None
    conoce_lineas_fomento: Optional[str] = None
    interes_formacion: Optional[bool] = None
    areas_capacitacion: Optional[str] = None
    interes_difusion: Optional[bool] = None
    interes_experto_iaavim: Optional[bool] = None
    
    # Subperfiles
    subperfiles_seleccionados: Optional[List[str]] = None
    
    # Consentimiento
    acepta_terminos: Optional[bool] = None
    portfolio_link: Optional[str] = None
    dni_adjunto_path: Optional[str] = None
    declaracion_inicial: Optional[bool] = None
    borrador: Optional[bool] = None


class PersonaFisicaOut(BaseModel):
    """Schema de salida para Persona Física"""
    id: int
    user_id: str
    
    # Datos personales - permitidos null para borradores
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    cuil: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    domicilio: Optional[str] = None
    municipio: Optional[str] = None
    distrito: Optional[str] = None
    
    # Educación
    nivel_educativo: Optional[str] = None
    trabajo_final: Optional[bool] = None
    titulo_tesis: Optional[str] = None
    
    # Identidades
    pueblo_originario: Optional[str] = None
    cual_pueblo: Optional[str] = None
    afrodescendiente: Optional[str] = None
    lgbtiq: Optional[str] = None
    discapacidad: Optional[str] = None
    tipo_discapacidad: Optional[str] = None
    personas_a_cargo: Optional[bool] = None
    tipo_personas_a_cargo: Optional[List[str]] = None
    otros_personas_a_cargo: Optional[str] = None
    
    # Laboral
    principal_fuente_audiovisual: Optional[bool] = None
    otra_fuente: Optional[str] = None
    relacion_laboral: Optional[str] = None
    otra_relacion: Optional[str] = None
    inscripto_afip: Optional[str] = None
    situacion_iva: Optional[str] = None
    pertenece_red: Optional[bool] = None
    nombre_red: Optional[str] = None
    
    # Interés institucional
    proyectos_iaavim: Optional[bool] = None
    conoce_lineas_fomento: Optional[str] = None
    interes_formacion: Optional[bool] = None
    areas_capacitacion: Optional[str] = None
    interes_difusion: Optional[bool] = None
    interes_experto_iaavim: Optional[bool] = None
    
    # Subperfiles
    subperfiles_seleccionados: Optional[List[str]] = None
    
    # Consentimiento
    acepta_terminos: bool
    portfolio_link: Optional[str] = None
    dni_adjunto_path: Optional[str] = None
    declaracion_inicial: bool
    borrador: bool = False
    
    # Metadatos
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# === SCHEMAS PARA SUBPERFILES (CRUD individual) ===
class ObraSubperfilCreate(ObraSubperfilBase):
    pass

class ObraSubperfilOut(ObraSubperfilBase):
    id: int
    persona_fisica_id: int
    
    model_config = ConfigDict(from_attributes=True)

class TecnicoArtisticoCreate(TecnicoArtisticoBase):
    pass

class TecnicoArtisticoOut(TecnicoArtisticoBase):
    id: int
    persona_fisica_id: int
    
    model_config = ConfigDict(from_attributes=True)

class CapacitadorCreate(CapacitadorBase):
    pass

class CapacitadorOut(CapacitadorBase):
    id: int
    persona_fisica_id: int
    
    model_config = ConfigDict(from_attributes=True)

class InvestigadorCreate(InvestigadorBase):
    pass

class InvestigadorOut(InvestigadorBase):
    id: int
    persona_fisica_id: int
    
    model_config = ConfigDict(from_attributes=True)
