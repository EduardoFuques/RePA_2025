# models/persona_juridica_model.py
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


class PersonaJuridica(Base):
    """
    Modelo para Persona Jurídica del RePA.
    Corresponde al formulario PJ del frontend.
    """

    __tablename__ = "personas_juridicas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # === DATOS INSTITUCIONALES ===
    nombre_pj = Column(String(255), nullable=True)  # nullable para borrador
    cuit = Column(String(15), unique=True, nullable=True)  # nullable para borrador
    figura_legal = Column(String(50), nullable=True)  # nullable para borrador
    # Opciones: sa, srl, sas, cooperativa, fundacion, asociacion_civil, otra
    otra_figura_legal = Column(String(100), nullable=True)
    fecha_constitucion = Column(Date, nullable=True)
    objeto_social = Column(Text, nullable=True)

    # === DOMICILIO Y CONTACTO ===
    domicilio_legal = Column(String(255), nullable=True)  # nullable para borrador
    localidad = Column(String(100), nullable=True)  # nullable para borrador
    distrito = Column(String(50), nullable=True)  # nullable para borrador
    telefono_institucional = Column(String(30), nullable=True)  # nullable para borrador
    email_contacto = Column(String(255), nullable=True)  # nullable para borrador
    web_redes = Column(JSON, nullable=True)  # Array de URLs

    # === REPRESENTACIÓN LEGAL ===
    nombre_representante = Column(String(200), nullable=True)  # nullable para borrador
    dni_representante = Column(String(20), nullable=True)  # nullable para borrador
    cargo_representante = Column(String(100), nullable=True)  # nullable para borrador
    telefono_representante = Column(String(30), nullable=True)  # nullable para borrador
    email_representante = Column(String(255), nullable=True)  # nullable para borrador
    vincular_personas = Column(String(10), nullable=True)  # si, no

    # === ACTIVIDADES AUDIOVISUALES ===
    actividades_principales = Column(JSON, nullable=True)
    # Opciones: produccion, distribucion, exhibicion, formacion, otra
    otra_actividad = Column(String(255), nullable=True)
    lineas_trabajo = Column(Text, nullable=True)
    apoyo_iaavim = Column(String(10), nullable=True)  # si, no
    descripcion_apoyo = Column(Text, nullable=True)
    otros_registros = Column(String(10), nullable=True)  # si, no
    cuales_registros = Column(String(255), nullable=True)

    # === DOCUMENTACIÓN (paths a archivos) ===
    estatuto_path = Column(String(500), nullable=True)
    constancia_cuit_path = Column(String(500), nullable=True)
    acta_autoridades_path = Column(String(500), nullable=True)
    cv_institucional_path = Column(String(500), nullable=True)

    # === CONSENTIMIENTO ===
    consentimiento = Column(Boolean, nullable=False, default=False)
    declaracion_inicial = Column(Boolean, nullable=False, default=False)
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario
    user = relationship("User", back_populates="persona_juridica")


class IntegrantePJ(Base):
    """Integrantes vinculados al RePA de una Persona Jurídica"""

    __tablename__ = "integrantes_pj"

    id = Column(Integer, primary_key=True, index=True)
    persona_juridica_id = Column(
        Integer, ForeignKey("personas_juridicas.id"), nullable=False
    )

    nombre = Column(String(200), nullable=False)
    dni = Column(String(20), nullable=True)
    cargo = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    vinculado_repa = Column(Boolean, default=False)  # Si ya está registrado en RePA

    persona_juridica = relationship("PersonaJuridica", backref="integrantes")
