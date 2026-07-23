# models/obra_audiovisual_model.py
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from src.database import Base
from src.models.registro_lifecycle import RegistroLifecycleMixin


class ObraAudiovisual(RegistroLifecycleMixin, Base):
    """
    Modelo para Obras Audiovisuales del AGAM (Archivo General Audiovisual Misionero).
    Corresponde al formulario AGAM del frontend.
    """

    __tablename__ = "obras_audiovisuales"
    __table_args__ = (
        CheckConstraint(
            "tipo_produccion IN ('independiente', 'comunitario', 'institucional', "
            "'publicitario', 'otro')",
            name="ck_obras_audiovisuales_tipo_produccion",
        ),
        CheckConstraint(
            "medio IN ('cine', 'tv', 'digital', 'videojuego', 'otro')",
            name="ck_obras_audiovisuales_medio",
        ),
        CheckConstraint(
            "extension IN ('cortometraje', 'mediometraje', 'largometraje')",
            name="ck_obras_audiovisuales_extension",
        ),
        CheckConstraint(
            "formato_narrativo IN ('unitario', 'serie', 'miniserie')",
            name="ck_obras_audiovisuales_formato_narrativo",
        ),
        CheckConstraint(
            "genero IN ('ficcion', 'documental', 'animacion', 'experimental', 'otro')",
            name="ck_obras_audiovisuales_genero",
        ),
        CheckConstraint(
            "resolucion IN ('sd', 'hd', 'full_hd', '2k', '4k')",
            name="ck_obras_audiovisuales_resolucion",
        ),
        CheckConstraint(
            "registro_obra_nacional IN ('si', 'no', 'en_tramite')",
            name="ck_obras_audiovisuales_registro_obra_nacional",
        ),
    )

    # Tipo de entidad para la emisión del código RePA.
    REPA_TIPO = "AGAM"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )  # Usuario que registra

    # AGAM no emite código RePA propio (ver RegistroLifecycleMixin.codigo_repa,
    # que queda NULL acá): usa como "código de trámite" el codigo_repa de la
    # Persona Física que la presenta. No es unique porque un mismo user puede
    # tener varias obras, todas con el mismo código de trámite.
    codigo_repa_titular = Column(String(30), nullable=True)

    # === IDENTIFICACIÓN ===
    codigo_agam = Column(
        String(50), unique=True, nullable=True
    )  # Código asignado por AGAM
    titulo = Column(String(255), nullable=True)
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
    # Opciones: cine, tv, digital, videojuego, otro

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

    # === ESTADO ===
    borrador = Column(
        Boolean, default=True, nullable=False
    )  # True = draft, False = submitted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relación con el usuario (user_id; revisado_por es otra FK a users)
    user = relationship(
        "User", back_populates="obras_audiovisuales", foreign_keys=[user_id]
    )

    # Relaciones con Exhibiciones
    exhibiciones = relationship("Exhibicion", back_populates="obra")


class EquipoTecnicoObra(Base):
    """Equipo técnico de una obra audiovisual"""

    __tablename__ = "equipo_tecnico_obra"

    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(
        Integer,
        ForeignKey("obras_audiovisuales.id", ondelete="CASCADE"),
        nullable=False,
    )

    rol = Column(String(100), nullable=False)
    # Roles: direccion, produccion_ejecutiva, direccion_fotografia, direccion_arte,
    # montaje_edicion, sonido, guion, actuacion_principal_1, actuacion_principal_2
    nombre = Column(String(200), nullable=False)
    en_repa = Column(String(10), nullable=True)  # si, no
    codigo_repa = Column(String(50), nullable=True)  # Si está en RePA

    obra = relationship(
        "ObraAudiovisual",
        backref=backref(
            "equipo_tecnico", cascade="all, delete-orphan", passive_deletes=True
        ),
    )
