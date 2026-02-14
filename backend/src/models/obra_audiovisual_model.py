# models/obra_audiovisual_model.py
from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database import Base


class ObraAudiovisual(Base):
    """
    Modelo para Obras Audiovisuales del AGAM (Archivo General Audiovisual Misionero).
    Corresponde al formulario AGAM del frontend.
    """

    __tablename__ = "obras_audiovisuales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False
    )  # Usuario que registra

    # === IDENTIFICACIÓN ===
    codigo_agam = Column(
        String(50), unique=True, nullable=True
    )  # Código asignado por AGAM
    titulo = Column(String(255), nullable=False)
    anio_estreno = Column(Integer, nullable=True)
    anio_ingreso = Column(Integer, nullable=True)  # Año de ingreso al AGAM
    duracion_minutos = Column(Integer, nullable=True)
    tipo_produccion = Column(String(50), nullable=True)
    # Opciones: independiente, comunitario, institucional, publicitario, otro
    extension = Column(String(30), nullable=True)
    # Opciones: cortometraje, mediometraje, largometraje
    formato_narrativo = Column(String(30), nullable=True)
    # Opciones: unitario, serie, miniserie
    genero = Column(String(50), nullable=True)
    # Opciones: ficcion, documental, animacion, experimental, otro
    subgenero = Column(String(100), nullable=True)
    medio = Column(String(30), nullable=True)
    # Opciones: cine, television, digital, otro

    # === DATOS TÉCNICOS ===
    formatos_disponibles = Column(JSON, nullable=True)
    # Opciones: 35mm, 16mm, super8, betacam, dvcam, hdv, mp4_avi, otro
    otro_formato = Column(String(100), nullable=True)
    resolucion = Column(String(20), nullable=True)
    # Opciones: sd, hd, full_hd, 2k, 4k
    idioma_original = Column(String(50), nullable=True)
    subtitulos = Column(String(100), nullable=True)
    uso_material = Column(JSON, nullable=True)
    # Opciones: exhibicion, investigacion, educativo, otro
    otro_uso = Column(String(255), nullable=True)
    ficha_tecnica_path = Column(String(500), nullable=True)
    ubicacion = Column(String(255), nullable=True)  # Ubicación física en archivo

    # === DATOS RELACIONALES ===
    productora_responsable = Column(String(255), nullable=True)
    codigo_repa_productora = Column(String(50), nullable=True)  # Si está en RePA
    participo_fomento = Column(String(10), nullable=True)  # si, no
    lineas_fomento = Column(JSON, nullable=True)
    # Opciones: produccion, postproduccion, desarrollo, distribucion, otro
    otro_fomento = Column(String(255), nullable=True)
    registro_obra_nacional = Column(String(20), nullable=True)
    # Opciones: si, no, en_tramite
    vinculos_areas = Column(JSON, nullable=True)
    # Opciones: exhibicion, capacitacion, investigacion, otro

    # === DERECHOS ===
    autoriza_exhibicion = Column(String(10), nullable=True)  # si, no
    autoriza_investigacion = Column(String(10), nullable=True)  # si, no
    convenio_cesion = Column(String(10), nullable=True)  # si, no
    archivo_convenio_path = Column(String(500), nullable=True)
    restricciones = Column(Text, nullable=True)

    # Relación con el usuario
    user = relationship("User", back_populates="obras_audiovisuales")

    # Relaciones con Exhibiciones y Cinemateca
    exhibiciones = relationship("Exhibicion", back_populates="obra")
    registros_cinemateca = relationship("Cinemateca", back_populates="obra")


class EquipoTecnicoObra(Base):
    """Equipo técnico de una obra audiovisual"""

    __tablename__ = "equipo_tecnico_obra"

    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(Integer, ForeignKey("obras_audiovisuales.id"), nullable=False)

    rol = Column(String(100), nullable=False)
    # Roles: direccion, produccion_ejecutiva, direccion_fotografia, direccion_arte,
    # montaje_edicion, sonido, guion, actuacion_principal_1, actuacion_principal_2
    nombre = Column(String(200), nullable=False)
    en_repa = Column(String(10), nullable=True)  # si, no
    codigo_repa = Column(String(50), nullable=True)  # Si está en RePA

    obra = relationship("ObraAudiovisual", backref="equipo_tecnico")
