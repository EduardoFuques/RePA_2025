# models/person_model.py
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.database import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)  # Relación 1 a 1
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni_cuit_cuil = Column(String, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    nacionalidad = Column(String, nullable=True)
    identidad_genero = Column(String, nullable=True)
    etnia = Column(Boolean, default=True)
    etnia_nombre = Column(String, nullable=True)
    estado_civil = Column(String, nullable=True)
    educacion_nivel = Column(String, nullable=True)
    educacion_titulo = Column(String, nullable=True)
    educacion_institucion = Column(String, nullable=True)
    personas_a_cargo = Column(Integer, default=0)
    tipo_contribuyente = Column(String, nullable=True)
    actividad_registrada = Column(String, nullable=True)
    telefono = Column(String, nullable=False)
    dir_calle = Column(String, nullable=True)
    dir_numero = Column(String, nullable=True)
    dir_piso = Column(String, nullable=True)
    dir_letra_nro_depto = Column(String, nullable=True)
    dir_cp = Column(String, nullable=True)
    dir_localidad = Column(String, nullable=True)
    dir_departamento = Column(String, nullable=True)
    dir_provincia = Column(String, nullable=True)
    dir_pais = Column(String, nullable=True)

    # Relación con el usuario
    user = relationship("User", back_populates="person", foreign_keys=[user_id])
