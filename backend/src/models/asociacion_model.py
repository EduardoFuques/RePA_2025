# models/asociacion_model.py
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from src.database import Base
from src.models.registro_lifecycle import RegistroLifecycleMixin


class Asociacion(RegistroLifecycleMixin, Base):
    """
    Modelo para Asociación/Colectivo del RePA.
    Corresponde al formulario AS del frontend.
    """

    __tablename__ = "asociaciones"

    # Tipo de entidad para la emisión del código RePA.
    REPA_TIPO = "AS"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # AS no emite código RePA propio (ver RegistroLifecycleMixin.codigo_repa,
    # que queda NULL acá): usa como "código de trámite" el codigo_repa de la
    # Persona Física que la presenta. No es unique porque una misma PF puede
    # presentar varios registros con el mismo código de trámite.
    codigo_repa_titular = Column(String(30), nullable=True)

    # === DATOS BÁSICOS Y CONTACTO ===
    nombre_asociacion = Column(String(255), nullable=True)  # nullable para borrador
    anio_creacion = Column(Integer, nullable=True)
    personeria_juridica = Column(String(10), nullable=True)  # si, no, en_tramite
    tipo_personeria = Column(String(50), nullable=True)
    otra_personeria = Column(String(100), nullable=True)
    cuit = Column(String(15), unique=True, nullable=True)
    domicilio = Column(String(255), nullable=True)  # nullable para borrador
    localidad = Column(String(100), nullable=True)  # nullable para borrador
    distrito = Column(String(50), nullable=True)  # nullable para borrador
    telefono = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)  # nullable para borrador
    web = Column(String(500), nullable=True)

    # === REPRESENTACIÓN ===
    nombre_referente = Column(String(200), nullable=True)  # nullable para borrador
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
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario (user_id; revisado_por es otra FK a users)
    user = relationship("User", back_populates="asociacion", foreign_keys=[user_id])


class IntegranteAsociacion(Base):
    """Integrantes vinculados al RePA de una Asociación/Colectivo"""

    __tablename__ = "integrantes_asociacion"

    id = Column(Integer, primary_key=True, index=True)
    asociacion_id = Column(
        Integer, ForeignKey("asociaciones.id", ondelete="CASCADE"), nullable=False
    )

    nombre = Column(String(200), nullable=False)
    dni = Column(String(20), nullable=True)
    rol = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    vinculado_repa = Column(Boolean, default=False)

    asociacion = relationship(
        "Asociacion",
        backref=backref(
            "integrantes", cascade="all, delete-orphan", passive_deletes=True
        ),
    )
