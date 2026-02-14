# models/rodaje_model.py
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

from src.database import Base


class Rodaje(Base):
    """
    Modelo para Comisión de Filmaciones - Archivo de Rodajes de Misiones.
    Registra, gestiona y monitorea los rodajes audiovisuales realizados en la provincia.
    """

    __tablename__ = "rodajes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # === 1. TIPO DE REGISTRO ===
    tipo_registro = Column(String(30), nullable=True)
    # Opciones: alta_rodaje, finalizacion_rodaje

    # === 2. DATOS GENERALES DEL PROYECTO ===
    titulo_produccion = Column(String(255), nullable=True)
    tipo_produccion = Column(String(50), nullable=True)
    # Opciones: largometraje, serie, publicidad, documental, videoclip, videojuego, otro
    otro_tipo_produccion = Column(String(100), nullable=True)
    genero = Column(String(100), nullable=True)
    clasificacion = Column(String(50), nullable=True)
    # Opciones: ficcion, documental, animacion, experimental, otro
    otra_clasificacion = Column(String(100), nullable=True)
    pais_produccion = Column(String(100), nullable=True)
    idioma_original = Column(String(50), nullable=True)
    sinopsis = Column(Text, nullable=True)  # máx 500 caracteres
    anio_rodaje = Column(Integer, nullable=True)  # obligatorio para estadísticas
    codigo_repa_productora = Column(String(50), nullable=True)
    codigos_repa_responsables = Column(JSON, nullable=True)  # Lista de códigos RePA
    id_proyecto_fomento = Column(String(50), nullable=True)  # Si proviene de Fomento

    # === 3. PRODUCTORA RESPONSABLE ===
    nombre_productora = Column(String(255), nullable=True)
    cuit_productora = Column(String(13), nullable=True)
    representante_legal = Column(String(200), nullable=True)
    productor_campo = Column(String(200), nullable=True)  # Contacto 24h
    email_productora = Column(String(255), nullable=True)
    telefono_productora = Column(String(50), nullable=True)
    provincia_pais_origen = Column(String(100), nullable=True)

    # === 4. INFORMACIÓN DEL RODAJE ===
    fecha_inicio_rodaje = Column(Date, nullable=True)
    fecha_fin_rodaje = Column(Date, nullable=True)
    locaciones = Column(JSON, nullable=True)
    # Lista de objetos: {municipio, direccion, espacio, num_personas, servicios_requeridos}
    cantidad_permisos = Column(Integer, nullable=True)
    vehiculos_equipamiento = Column(Text, nullable=True)  # grúas, drones, generadores

    # === 5. CARTA DE AVAL / ACOMPAÑAMIENTO INSTITUCIONAL ===
    requiere_carta_aval = Column(Boolean, default=False)
    destino_aval = Column(String(50), nullable=True)
    # Opciones: festival, privado, coproduccion, otro
    otro_destino_aval = Column(String(100), nullable=True)
    motivo_aval = Column(Text, nullable=True)
    fecha_limite_aval = Column(Date, nullable=True)
    # Documentos adjuntos se manejan por upload_routes

    # === 6. DOCUMENTACIÓN OBLIGATORIA (Alta de rodaje) ===
    tiene_poliza_seguro = Column(Boolean, default=False)
    tiene_acuerdo_indemnizacion = Column(Boolean, default=False)
    tiene_autorizaciones_privados = Column(Boolean, default=False)
    tiene_fotos_locaciones = Column(Boolean, default=False)
    tiene_permisos_especiales = Column(Boolean, default=False)
    documentos_adjuntos = Column(JSON, nullable=True)  # Lista de paths de archivos

    # === 7. IMPACTO Y CIERRE (Finalización de rodaje) ===
    fecha_real_finalizacion = Column(Date, nullable=True)
    cantidad_tecnicos_locales = Column(Integer, nullable=True)
    cantidad_artistas_locales = Column(Integer, nullable=True)
    descripcion_beneficios_locales = Column(Text, nullable=True)
    medidas_ambientales = Column(Text, nullable=True)
    compromisos_comunitarios = Column(Text, nullable=True)
    informe_rodaje = Column(String(500), nullable=True)  # Path al archivo

    # === 8. SEGUIMIENTO Y AUTORIZACIONES ===
    estado_tramite = Column(String(30), default="recibido")
    # Opciones: recibido, en_evaluacion, aprobado, condicionado, denegado, finalizado
    fecha_evaluacion = Column(Date, nullable=True)
    fecha_emision_permiso = Column(Date, nullable=True)
    tarifas_aplicadas = Column(Text, nullable=True)
    pagos_realizados = Column(Text, nullable=True)
    inspector_asignado = Column(String(200), nullable=True)
    informe_inspeccion = Column(Text, nullable=True)
    observaciones_internas = Column(Text, nullable=True)

    # === METADATOS ===
    borrador = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relación con el usuario
    user = relationship("User", back_populates="rodajes")
