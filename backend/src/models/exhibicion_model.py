# models/exhibicion_model.py
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class Sala(Base):
    """
    Modelo para Salas de Exhibición.
    Espacios donde se proyectan obras audiovisuales.
    """

    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # === DATOS BÁSICOS ===
    nombre = Column(String(255), nullable=True)  # nullable para borrador
    tipo_sala = Column(String(50), nullable=True)  # nullable para borrador
    # Opciones: cine_comercial, cine_arte, espacio_cultural, auditorio, aire_libre, otro
    otro_tipo = Column(String(100), nullable=True)

    # === UBICACIÓN ===
    domicilio = Column(String(255), nullable=True)  # nullable para borrador
    localidad = Column(String(100), nullable=True)  # nullable para borrador
    distrito = Column(String(50), nullable=True)  # nullable para borrador

    # === CARACTERÍSTICAS TÉCNICAS ===
    capacidad = Column(Integer, nullable=True)
    tiene_proyector_digital = Column(Boolean, default=False)
    tiene_proyector_35mm = Column(Boolean, default=False)
    tiene_sonido_dolby = Column(Boolean, default=False)
    tiene_accesibilidad = Column(Boolean, default=False)
    otras_caracteristicas = Column(Text, nullable=True)

    # === CONTACTO ===
    nombre_responsable = Column(String(200), nullable=True)
    telefono = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    web = Column(String(500), nullable=True)

    # === RESPONSABLE LEGAL ===
    responsable_legal = Column(JSON, nullable=True)  # {nombre, apellido, dni, cuil, email, telefono}

    # === PROGRAMADOR ===
    programador = Column(JSON, nullable=True)  # {tieneProgramador, datos: [{nombre, email, telefono}]}

    # === RESPONSABLE TÉCNICO ===
    responsable_tecnico = Column(JSON, nullable=True)  # {nombre, distrito, email, telefono}

    # === AFILIACIONES Y REDES ===
    afiliaciones = Column(JSON, nullable=True)  # {integraRed, redesDescripcion, esSedeFestival, nombreFestival, tieneConvenio}

    # === CONSENTIMIENTO ===
    consentimiento = Column(Boolean, default=False)

    # === METADATOS ===
    activo = Column(Boolean, default=True)
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario
    user = relationship("User", back_populates="salas")
    # Relación con exhibiciones
    exhibiciones = relationship("Exhibicion", back_populates="sala")


class Exhibicion(Base):
    """
    Modelo para Exhibiciones de obras audiovisuales.
    Registro de proyecciones en salas.
    """

    __tablename__ = "exhibiciones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    obra_id = Column(Integer, ForeignKey("obras_audiovisuales.id"), nullable=True)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=True)

    # === DATOS DE LA EXHIBICIÓN ===
    titulo_obra = Column(
        String(255), nullable=True
    )  # nullable para borrador  # Por si no está en AGAM
    fecha_exhibicion = Column(Date, nullable=True)  # nullable para borrador
    cantidad_funciones = Column(Integer, default=1)

    # === TIPO DE EXHIBICIÓN ===
    tipo_exhibicion = Column(String(50), nullable=True)  # nullable para borrador
    # Opciones: estreno, reestreno, ciclo, festival, especial, otro
    nombre_evento = Column(
        String(255), nullable=True
    )  # Si es parte de un ciclo/festival

    # === ESPECTADORES ===
    espectadores_total = Column(Integer, nullable=True)
    espectadores_pagos = Column(Integer, nullable=True)
    espectadores_gratuitos = Column(Integer, nullable=True)
    espectadores_abonados = Column(Integer, nullable=True)

    # === RECAUDACIÓN ===
    recaudacion_total = Column(Float, nullable=True)
    precio_entrada_general = Column(Float, nullable=True)

    # === OBSERVACIONES ===
    observaciones = Column(Text, nullable=True)

    # === METADATOS ===
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones
    user = relationship("User", back_populates="exhibiciones")
    obra = relationship("ObraAudiovisual", back_populates="exhibiciones")
    sala = relationship("Sala", back_populates="exhibiciones")


class Festival(Base):
    """
    Modelo para Festivales de cine y audiovisual.
    """

    __tablename__ = "festivales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # === DATOS BÁSICOS ===
    nombre = Column(String(255), nullable=True)  # nullable para borrador
    edicion = Column(Integer, nullable=True)  # Número de edición
    fecha_inicio = Column(Date, nullable=True)  # nullable para borrador
    fecha_fin = Column(Date, nullable=True)

    # === UBICACIÓN ===
    localidad = Column(String(100), nullable=True)  # nullable para borrador
    distrito = Column(String(50), nullable=True)  # nullable para borrador
    sedes = Column(JSON, nullable=True)  # Lista de sedes/salas

    # === CARACTERÍSTICAS ===
    tipo_festival = Column(String(50), nullable=True)
    # Opciones: competitivo, no_competitivo, mixto
    categorias = Column(JSON, nullable=True)
    # Opciones: ficcion, documental, animacion, cortometraje, largometraje, etc.
    tematica = Column(String(255), nullable=True)

    # === PARTICIPACIÓN ===
    cantidad_obras_seleccionadas = Column(Integer, nullable=True)
    cantidad_obras_misioneras = Column(Integer, nullable=True)
    cantidad_espectadores = Column(Integer, nullable=True)

    # === CONTACTO ===
    organizador = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    telefono = Column(String(30), nullable=True)
    web = Column(String(500), nullable=True)

    # === DATOS ADICIONALES ===
    periodicidad = Column(String(50), nullable=True)  # anual, bianual, etc.
    anio_inicio = Column(Integer, nullable=True)
    responsable = Column(JSON, nullable=True)  # {tipo: [], nombreRazon, dniCuit, email, telefono}
    curaduria = Column(Boolean, default=False)
    calendario_oficial = Column(Boolean, default=False)

    # === APOYO INSTITUCIONAL ===
    apoyo_iaavim = Column(Boolean, default=False)
    tipo_apoyo = Column(String(255), nullable=True)

    # === CONSENTIMIENTO ===
    consentimiento = Column(Boolean, default=False)
    desea_recibir_info = Column(Boolean, default=False)

    # === METADATOS ===
    activo = Column(Boolean, default=True)
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario
    user = relationship("User", back_populates="festivales")


class Cinemateca(Base):
    """
    Modelo para registros de Cinemateca.
    Gestión del archivo físico de obras audiovisuales.
    """

    __tablename__ = "cinemateca"

    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(
        Integer, ForeignKey("obras_audiovisuales.id"), nullable=True
    )  # nullable para borrador

    # === DATOS DEL SOPORTE ===
    tipo_soporte = Column(String(50), nullable=True)  # nullable para borrador
    # Opciones: 35mm, 16mm, super8, betacam, dvcam, dvd, bluray, digital, otro
    otro_soporte = Column(String(100), nullable=True)
    cantidad_copias = Column(Integer, default=1)

    # === ESTADO DE CONSERVACIÓN ===
    estado_conservacion = Column(String(30), nullable=True)  # nullable para borrador
    # Opciones: excelente, bueno, regular, malo, critico
    requiere_restauracion = Column(Boolean, default=False)
    observaciones_estado = Column(Text, nullable=True)

    # === UBICACIÓN FÍSICA ===
    ubicacion_fisica = Column(String(255), nullable=True)  # nullable para borrador
    estanteria = Column(String(50), nullable=True)
    caja = Column(String(50), nullable=True)

    # === DIGITALIZACIÓN ===
    digitalizado = Column(Boolean, default=False)
    formato_digital = Column(String(50), nullable=True)
    ubicacion_digital = Column(String(500), nullable=True)  # Path o URL

    # === PRÉSTAMOS ===
    disponible_prestamo = Column(Boolean, default=True)
    en_prestamo = Column(Boolean, default=False)
    fecha_ultimo_prestamo = Column(Date, nullable=True)

    # === METADATOS ===
    fecha_ingreso = Column(Date, nullable=True)
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con la obra
    obra = relationship("ObraAudiovisual", back_populates="registros_cinemateca")
