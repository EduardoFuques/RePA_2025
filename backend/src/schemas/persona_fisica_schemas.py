# schemas/persona_fisica_schemas.py
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    nivel_educativo: str | None = None
    trabajo_final: bool | None = None
    titulo_tesis: str | None = None


# === IDENTIDADES ===
class IdentidadesBase(BaseModel):
    pueblo_originario: str | None = None  # si, no, prefiere_no_responder
    cual_pueblo: str | None = None
    afrodescendiente: str | None = None  # si, no, prefiere_no_responder
    lgbtiq: str | None = None  # si, no, prefiere_no_responder
    discapacidad: str | None = None  # si, no, prefiere_no_responder
    tipo_discapacidad: str | None = None
    personas_a_cargo: bool | None = None
    tipo_personas_a_cargo: list[str] | None = None
    otros_personas_a_cargo: str | None = None


# === LABORAL ===
class LaboralBase(BaseModel):
    principal_fuente_audiovisual: bool | None = None
    otra_fuente: str | None = None
    relacion_laboral: str | None = None
    otra_relacion: str | None = None
    inscripto_afip: str | None = None
    situacion_iva: str | None = None
    pertenece_red: bool | None = None
    nombre_red: str | None = None


# === INTERÉS INSTITUCIONAL ===
class InteresBase(BaseModel):
    proyectos_iaavim: bool | None = None
    conoce_lineas_fomento: str | None = None  # si, no, parcialmente
    interes_formacion: bool | None = None
    areas_capacitacion: str | None = None
    interes_difusion: bool | None = None
    interes_experto_iaavim: bool | None = None


# === SUBPERFILES ===
class ObraSubperfilBase(BaseModel):
    titulo_obra: str = Field(..., min_length=1, max_length=255)
    anio: int | None = None
    rol: str | None = None


class TecnicoArtisticoBase(BaseModel):
    areas: list[str] | None = None
    medios: list[str] | None = None
    obras_iaavim: list[str] | None = None
    especializaciones: list[str] | None = None


class CapacitadorBase(BaseModel):
    capacitaciones_iaavim: bool = False
    capacitaciones: list[dict] | None = None
    capacitador_actual: bool = False
    areas_capacitacion: str | None = None
    publico_destinatario: str | None = None
    tipos_instituciones: list[str] | None = None
    disena_contenidos: bool = False
    interes_lista_expertos: bool = False
    cv_link: str | None = None
    materiales_link: str | None = None


class InvestigadorBase(BaseModel):
    participo_proyectos: bool = False
    proyectos: list[dict] | None = None
    tiene_publicaciones: bool = False
    publicaciones_link: str | None = None
    tematica_principal: str | None = None
    enfoque: str | None = None
    pertenece_grupo: bool = False
    nombre_grupo: str | None = None
    recibio_financiamiento: bool = False
    institucion_financiamiento: str | None = None
    interes_red_investigadores: bool = False


# === CONSENTIMIENTO ===
class ConsentimientoBase(BaseModel):
    acepta_terminos: bool = False
    portfolio_link: str | None = None


# === SCHEMA PRINCIPAL ===
class PersonaFisicaCreate(BaseModel):
    """Schema para crear una Persona Física"""

    declaracion_inicial: bool = True

    # Datos personales - permitidos null para borradores
    nombre: str | None = Field(None, max_length=100)
    apellido: str | None = Field(None, max_length=100)
    dni: str | None = Field(None, max_length=20)
    cuil: str | None = Field(None, max_length=15)
    fecha_nacimiento: date | None = None
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    domicilio: str | None = Field(None, max_length=255)
    municipio: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)

    # Educación
    nivel_educativo: str | None = None
    trabajo_final: bool | None = None
    titulo_tesis: str | None = None

    # Identidades
    pueblo_originario: str | None = None
    cual_pueblo: str | None = None
    afrodescendiente: str | None = None
    lgbtiq: str | None = None
    discapacidad: str | None = None
    tipo_discapacidad: str | None = None
    personas_a_cargo: bool | None = None
    tipo_personas_a_cargo: list[str] | None = None
    otros_personas_a_cargo: str | None = None

    # Laboral
    principal_fuente_audiovisual: bool | None = None
    otra_fuente: str | None = None
    relacion_laboral: str | None = None
    otra_relacion: str | None = None
    inscripto_afip: str | None = None
    situacion_iva: str | None = None
    pertenece_red: bool | None = None
    nombre_red: str | None = None

    # Interés institucional
    proyectos_iaavim: bool | None = None
    conoce_lineas_fomento: str | None = None
    interes_formacion: bool | None = None
    areas_capacitacion: str | None = None
    interes_difusion: bool | None = None
    interes_experto_iaavim: bool | None = None

    # Subperfiles
    subperfiles_seleccionados: list[str] | None = None

    # Consentimiento
    acepta_terminos: bool = False
    portfolio_link: str | None = None
    redes_sociales: list[str] | None = None
    dni_adjunto_path: str | None = None
    borrador: bool = False


class PersonaFisicaUpdate(BaseModel):
    """Schema para actualizar una Persona Física"""

    # Datos personales
    nombre: str | None = Field(None, max_length=100)
    apellido: str | None = Field(None, max_length=100)
    dni: str | None = Field(None, max_length=20)
    cuil: str | None = Field(None, max_length=15)
    fecha_nacimiento: date | None = None
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    domicilio: str | None = Field(None, max_length=255)
    municipio: str | None = Field(None, max_length=100)
    distrito: str | None = Field(None, max_length=50)

    # Educación
    nivel_educativo: str | None = None
    trabajo_final: bool | None = None
    titulo_tesis: str | None = None

    # Identidades
    pueblo_originario: str | None = None
    cual_pueblo: str | None = None
    afrodescendiente: str | None = None
    lgbtiq: str | None = None
    discapacidad: str | None = None
    tipo_discapacidad: str | None = None
    personas_a_cargo: bool | None = None
    tipo_personas_a_cargo: list[str] | None = None
    otros_personas_a_cargo: str | None = None

    # Laboral
    principal_fuente_audiovisual: bool | None = None
    otra_fuente: str | None = None
    relacion_laboral: str | None = None
    otra_relacion: str | None = None
    inscripto_afip: str | None = None
    situacion_iva: str | None = None
    pertenece_red: bool | None = None
    nombre_red: str | None = None

    # Interés institucional
    proyectos_iaavim: bool | None = None
    conoce_lineas_fomento: str | None = None
    interes_formacion: bool | None = None
    areas_capacitacion: str | None = None
    interes_difusion: bool | None = None
    interes_experto_iaavim: bool | None = None

    # Subperfiles
    subperfiles_seleccionados: list[str] | None = None

    # Consentimiento
    acepta_terminos: bool | None = None
    portfolio_link: str | None = None
    redes_sociales: list[str] | None = None
    dni_adjunto_path: str | None = None
    declaracion_inicial: bool | None = None
    borrador: bool | None = None


class PersonaFisicaOut(BaseModel):
    """Schema de salida para Persona Física"""

    id: int
    user_id: str

    # Datos personales - permitidos null para borradores
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
    cuil: str | None = None
    fecha_nacimiento: date | None = None
    email: str | None = None
    telefono: str | None = None
    domicilio: str | None = None
    municipio: str | None = None
    distrito: str | None = None

    # Educación
    nivel_educativo: str | None = None
    trabajo_final: bool | None = None
    titulo_tesis: str | None = None

    # Identidades
    pueblo_originario: str | None = None
    cual_pueblo: str | None = None
    afrodescendiente: str | None = None
    lgbtiq: str | None = None
    discapacidad: str | None = None
    tipo_discapacidad: str | None = None
    personas_a_cargo: bool | None = None
    tipo_personas_a_cargo: list[str] | None = None
    otros_personas_a_cargo: str | None = None

    # Laboral
    principal_fuente_audiovisual: bool | None = None
    otra_fuente: str | None = None
    relacion_laboral: str | None = None
    otra_relacion: str | None = None
    inscripto_afip: str | None = None
    situacion_iva: str | None = None
    pertenece_red: bool | None = None
    nombre_red: str | None = None

    # Interés institucional
    proyectos_iaavim: bool | None = None
    conoce_lineas_fomento: str | None = None
    interes_formacion: bool | None = None
    areas_capacitacion: str | None = None
    interes_difusion: bool | None = None
    interes_experto_iaavim: bool | None = None

    # Subperfiles
    subperfiles_seleccionados: list[str] | None = None

    # Consentimiento
    acepta_terminos: bool
    portfolio_link: str | None = None
    redes_sociales: list[str] | None = None
    dni_adjunto_path: str | None = None
    declaracion_inicial: bool
    borrador: bool = False

    # Metadatos
    created_at: datetime | None = None
    updated_at: datetime | None = None

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
