# models/persona_fisica_model.py
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Boolean, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class PersonaFisica(Base):
    """
    Modelo para Persona Física (Humana) del RePA.
    Corresponde al formulario PF del frontend.
    """
    __tablename__ = "personas_fisicas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    # === DATOS PERSONALES ===
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, nullable=False)
    cuil = Column(String(15), unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    email = Column(String(255), nullable=False)
    telefono = Column(String(30), nullable=False)
    domicilio = Column(String(255), nullable=False)
    municipio = Column(String(100), nullable=False)
    distrito = Column(String(50), nullable=False)
    
    # === EDUCACIÓN ===
    nivel_educativo = Column(String(50), nullable=True)
    # Opciones: primario_incompleto, primario_completo, secundario_incompleto, 
    # secundario_completo, terciario_incompleto, terciario_completo,
    # universitario_incompleto, universitario_completo, posgrado
    trabajo_final = Column(Boolean, nullable=True)
    titulo_tesis = Column(String(255), nullable=True)
    
    # === IDENTIDADES Y PERTENENCIAS ===
    pueblo_originario = Column(Boolean, nullable=True)
    cual_pueblo = Column(String(100), nullable=True)
    afrodescendiente = Column(String(30), nullable=True)  # si, no, prefiere_no_responder
    lgbtiq = Column(Boolean, nullable=True)
    discapacidad = Column(Boolean, nullable=True)
    tipo_discapacidad = Column(String(255), nullable=True)
    personas_a_cargo = Column(Boolean, nullable=True)
    tipo_personas_a_cargo = Column(JSON, nullable=True)  # Array: ['hijos', 'adultos_mayores', 'otros']
    otros_personas_a_cargo = Column(String(255), nullable=True)
    
    # === SITUACIÓN LABORAL Y FISCAL ===
    principal_fuente_audiovisual = Column(Boolean, nullable=True)
    otra_fuente = Column(String(255), nullable=True)
    relacion_laboral = Column(String(50), nullable=True)
    # Opciones: autonomo, relacion_dependencia, cooperativa, otro
    otra_relacion = Column(String(255), nullable=True)
    inscripto_afip = Column(Boolean, nullable=True)
    situacion_iva = Column(String(30), nullable=True)  # responsable_inscripto, monotributo, exento
    pertenece_red = Column(Boolean, nullable=True)
    nombre_red = Column(String(255), nullable=True)
    
    # === ÁREAS DE INTERÉS INSTITUCIONAL ===
    proyectos_iaavim = Column(Boolean, nullable=True)
    conoce_lineas_fomento = Column(Boolean, nullable=True)
    interes_formacion = Column(Boolean, nullable=True)
    areas_capacitacion = Column(Text, nullable=True)
    interes_difusion = Column(Boolean, nullable=True)
    interes_experto_iaavim = Column(Boolean, nullable=True)
    
    # === SUBPERFILES SELECCIONADOS ===
    # Array de subperfiles: ['productor', 'director', 'guionista', 'documentalista', 
    # 'realizadorIntegral', 'tecnicoArtistico', 'capacitador', 'investigador']
    subperfiles_seleccionados = Column(JSON, nullable=True)
    
    # === CONSENTIMIENTO ===
    acepta_terminos = Column(Boolean, nullable=False, default=False)
    portfolio_link = Column(String(500), nullable=True)
    dni_adjunto_path = Column(String(500), nullable=True)
    
    # === METADATOS ===
    declaracion_inicial = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relación con el usuario
    user = relationship("User", back_populates="persona_fisica")


class SubperfilProductor(Base):
    """Subperfil Productor - Obras producidas"""
    __tablename__ = "subperfil_productor"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), nullable=False)
    
    # Datos de la obra
    titulo_obra = Column(String(255), nullable=False)
    anio = Column(Integer, nullable=True)
    rol = Column(String(100), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="obras_productor")


class SubperfilDirector(Base):
    """Subperfil Director - Obras dirigidas"""
    __tablename__ = "subperfil_director"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), nullable=False)
    
    titulo_obra = Column(String(255), nullable=False)
    anio = Column(Integer, nullable=True)
    rol = Column(String(100), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="obras_director")


class SubperfilGuionista(Base):
    """Subperfil Guionista - Obras escritas"""
    __tablename__ = "subperfil_guionista"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), nullable=False)
    
    titulo_obra = Column(String(255), nullable=False)
    anio = Column(Integer, nullable=True)
    rol = Column(String(100), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="obras_guionista")


class SubperfilDocumentalista(Base):
    """Subperfil Documentalista - Documentales"""
    __tablename__ = "subperfil_documentalista"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), nullable=False)
    
    titulo_obra = Column(String(255), nullable=False)
    anio = Column(Integer, nullable=True)
    rol = Column(String(100), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="obras_documentalista")


class SubperfilRealizadorIntegral(Base):
    """Subperfil Realizador Integral - Obras como realizador integral"""
    __tablename__ = "subperfil_realizador_integral"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), nullable=False)
    
    titulo_obra = Column(String(255), nullable=False)
    anio = Column(Integer, nullable=True)
    rol = Column(String(100), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="obras_realizador_integral")


class SubperfilTecnicoArtistico(Base):
    """Subperfil Técnico/Artístico"""
    __tablename__ = "subperfil_tecnico_artistico"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), unique=True, nullable=False)
    
    # Arrays de opciones seleccionadas
    areas = Column(JSON, nullable=True)  # ['montaje', 'sonido', 'fotografia', etc.]
    medios = Column(JSON, nullable=True)
    obras_iaavim = Column(JSON, nullable=True)
    especializaciones = Column(JSON, nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="tecnico_artistico")


class SubperfilCapacitador(Base):
    """Subperfil Capacitador"""
    __tablename__ = "subperfil_capacitador"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), unique=True, nullable=False)
    
    capacitaciones_iaavim = Column(Boolean, default=False)
    capacitaciones = Column(JSON, nullable=True)  # Array de capacitaciones
    capacitador_actual = Column(Boolean, default=False)
    areas_capacitacion = Column(Text, nullable=True)
    publico_destinatario = Column(String(255), nullable=True)
    tipos_instituciones = Column(JSON, nullable=True)
    disena_contenidos = Column(Boolean, default=False)
    interes_lista_expertos = Column(Boolean, default=False)
    cv_link = Column(String(500), nullable=True)
    materiales_link = Column(String(500), nullable=True)
    
    persona_fisica = relationship("PersonaFisica", backref="capacitador")


class SubperfilInvestigador(Base):
    """Subperfil Investigador"""
    __tablename__ = "subperfil_investigador"
    
    id = Column(Integer, primary_key=True, index=True)
    persona_fisica_id = Column(Integer, ForeignKey("personas_fisicas.id"), unique=True, nullable=False)
    
    participo_proyectos = Column(Boolean, default=False)
    proyectos = Column(JSON, nullable=True)  # Array de proyectos
    tiene_publicaciones = Column(Boolean, default=False)
    publicaciones_link = Column(String(500), nullable=True)
    tematica_principal = Column(String(255), nullable=True)
    enfoque = Column(String(255), nullable=True)
    pertenece_grupo = Column(Boolean, default=False)
    nombre_grupo = Column(String(255), nullable=True)
    recibio_financiamiento = Column(Boolean, default=False)
    institucion_financiamiento = Column(String(255), nullable=True)
    interes_red_investigadores = Column(Boolean, default=False)
    
    persona_fisica = relationship("PersonaFisica", backref="investigador")
