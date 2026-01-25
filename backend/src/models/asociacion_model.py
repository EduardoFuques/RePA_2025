# models/asociacion_model.py
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Boolean, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class Asociacion(Base):
    """
    Modelo para Asociación/Colectivo del RePA.
    Corresponde al formulario AS del frontend.
    """
    __tablename__ = "asociaciones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    
    # === DATOS BÁSICOS Y CONTACTO ===
    nombre_asociacion = Column(String(255), nullable=False)
    anio_creacion = Column(Integer, nullable=True)
    personeria_juridica = Column(String(10), nullable=True)  # si, no, en_tramite
    tipo_personeria = Column(String(50), nullable=True)
    otra_personeria = Column(String(100), nullable=True)
    cuit = Column(String(15), nullable=True)
    domicilio = Column(String(255), nullable=False)
    localidad = Column(String(100), nullable=False)
    distrito = Column(String(50), nullable=False)
    telefono = Column(String(30), nullable=True)
    email = Column(String(255), nullable=False)
    web = Column(String(500), nullable=True)
    
    # === REPRESENTACIÓN ===
    nombre_referente = Column(String(200), nullable=False)
    rol_referente = Column(String(100), nullable=True)
    telefono_referente = Column(String(30), nullable=True)
    email_referente = Column(String(255), nullable=True)
    
    # === ÁMBITOS DE ACTUACIÓN ===
    ambito_produccion = Column(Boolean, default=False)
    ambito_formacion = Column(Boolean, default=False)
    ambito_exhibicion = Column(Boolean, default=False)
    ambito_comunicacion = Column(Boolean, default=False)
    ambito_distribucion = Column(Boolean, default=False)
    ambito_comunidad = Column(Boolean, default=False)
    ambito_investigacion = Column(Boolean, default=False)
    ambito_otro = Column(Boolean, default=False)
    otro_ambito = Column(String(255), nullable=True)
    
    # === OBJETIVOS E INTEGRANTES ===
    objetivos = Column(Text, nullable=True)
    cantidad_integrantes = Column(Integer, nullable=True)
    articulo_iaavim = Column(String(10), nullable=True)  # si, no
    descripcion_articulacion = Column(Text, nullable=True)
    info_adicional_integrantes = Column(Text, nullable=True)
    
    # === DOCUMENTACIÓN (paths a archivos) ===
    acta_constitucion_path = Column(String(500), nullable=True)
    declaracion_objetivos_path = Column(String(500), nullable=True)
    
    # === CONSENTIMIENTO ===
    consentimiento = Column(Boolean, nullable=False, default=False)
    declaracion_inicial = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relación con el usuario
    user = relationship("User", back_populates="asociacion")


class IntegranteAsociacion(Base):
    """Integrantes vinculados al RePA de una Asociación/Colectivo"""
    __tablename__ = "integrantes_asociacion"
    
    id = Column(Integer, primary_key=True, index=True)
    asociacion_id = Column(Integer, ForeignKey("asociaciones.id"), nullable=False)
    
    nombre = Column(String(200), nullable=False)
    dni = Column(String(20), nullable=True)
    rol = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    vinculado_repa = Column(Boolean, default=False)
    
    asociacion = relationship("Asociacion", backref="integrantes")
