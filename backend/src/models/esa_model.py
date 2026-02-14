# models/esa_model.py
from datetime import datetime, timezone

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


class EstudianteESA(Base):
    """
    Modelo para Estudiantes del Audiovisual (ESA).
    Registro independiente del RePA para estudiantes en formación.
    Vigencia: 1 año con renovación.
    """

    __tablename__ = "estudiantes_esa"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # === DATOS PERSONALES ===
    nombre_completo = Column(String(200), nullable=True)  # nullable para borrador
    dni = Column(String(20), unique=True, nullable=True)  # nullable para borrador
    cuil = Column(String(15), unique=True, nullable=True)  # nullable para borrador
    fecha_nacimiento = Column(Date, nullable=True)  # nullable para borrador
    genero = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)  # nullable para borrador
    telefono = Column(String(30), nullable=True)  # nullable para borrador

    # === LOCALIZACIÓN ===
    municipio = Column(String(100), nullable=True)  # nullable para borrador
    distrito = Column(
        String(20), nullable=True
    )  # nullable para borrador  # sur, norte, parana, uruguay

    # === DATOS DE FORMACIÓN ===
    institucion = Column(String(255), nullable=True)  # nullable para borrador
    otra_institucion = Column(String(255), nullable=True)  # Si eligió "Otra"
    carrera = Column(String(255), nullable=True)  # nullable para borrador
    anio_cursado = Column(Integer, nullable=True)
    modalidad = Column(
        String(20), nullable=True
    )  # nullable para borrador  # presencial, virtual, hibrido

    # === INTERESES Y PARTICIPACIÓN ===
    areas_interes = Column(JSON, nullable=True)
    # Opciones: direccion, produccion, guion, montaje, sonido, fotografia, animacion, arte, investigacion, otra
    otra_area = Column(String(255), nullable=True)
    participo_proyecto = Column(Boolean, nullable=True)
    descripcion_experiencia = Column(Text, nullable=True)

    # === DECLARACIONES ===
    estudiante_activo = Column(Boolean, nullable=False, default=False)
    leyo_reglamento = Column(Boolean, nullable=False, default=False)
    no_inscripto_repa = Column(Boolean, nullable=False, default=False)
    vigencia_un_anio = Column(Boolean, nullable=False, default=False)
    autoriza_datos = Column(Boolean, nullable=False, default=False)

    # === METADATOS ===
    fecha_alta = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_vencimiento = Column(DateTime, nullable=True)  # fecha_alta + 1 año
    activo = Column(Boolean, default=True)
    borrador = Column(Boolean, nullable=False, default=False)  # Para guardado parcial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario
    user = relationship("User", back_populates="estudiante_esa")
