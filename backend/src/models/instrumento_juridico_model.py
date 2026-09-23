# models/instrumento_juridico_model.py
"""
Modelo del Digesto Jurídico Institucional (Área de Asuntos Jurídicos - IAAviM).

Registra y tematiza todos los instrumentos legales generados o gestionados por
el Instituto, para consulta interna, rendición pública y trazabilidad con
proyectos y convenios asociados.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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


class InstrumentoJuridico(Base):
    """
    Instrumento legal del digesto jurídico (resolución, convenio, acta, etc.).

    Los enums se modelan como String + CheckConstraint (convención del repo):
    un sa.Enum crea un tipo nativo en PostgreSQL que después hay que migrar a
    mano cada vez que se agrega una opción al desplegable del formulario.
    """

    __tablename__ = "instrumentos_juridicos"
    __table_args__ = (
        CheckConstraint(
            "tipo_documento IN ('resolucion', 'convenio_aporte', 'convenio_marco', "
            "'acta_acuerdo_especifico', 'acta_consejo_directivo', 'dictamen', "
            "'contrato', 'carta_aval', 'otro')",
            name="ck_instrumentos_juridicos_tipo_documento",
        ),
        CheckConstraint(
            "ambito_aplicacion IN ('local', 'provincial', 'nacional', 'internacional')",
            name="ck_instrumentos_juridicos_ambito_aplicacion",
        ),
        CheckConstraint(
            "tematica_principal IN ('fomento_financiamiento', 'regulacion_normativa', "
            "'convenios_cooperacion', 'politicas_comunitarias', "
            "'regulacion_laboral_derechos_autor', 'lineamientos_institucionales', "
            "'otro')",
            name="ck_instrumentos_juridicos_tematica_principal",
        ),
        CheckConstraint(
            "estado_revision IN ('en_revision', 'validado', 'archivado')",
            name="ck_instrumentos_juridicos_estado_revision",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # === 1. DATOS GENERALES DEL INSTRUMENTO ===
    # nullable para borrador: el autoguardado crea la fila apenas se empieza
    # a cargar, igual que en los formularios del Padron. La obligatoriedad se
    # valida al ENVIAR (borrador=False), no en el esquema.
    tipo_documento = Column(String(50), nullable=True, index=True)
    # Opciones: resolucion, convenio_aporte, convenio_marco,
    # acta_acuerdo_especifico, acta_consejo_directivo, dictamen, contrato,
    # carta_aval, otro
    otro_tipo_documento = Column(String(100), nullable=True)
    numero_instrumento = Column(String(100), nullable=True, index=True)
    # Indexado: el doc pide búsqueda por número, es uno de los filtros centrales.
    version = Column(String(50), nullable=True)
    # Campo simple de la sección 1 (número o fecha de actualización). El bloque
    # de "control de versiones" de la sección 6 queda para una versión posterior.
    fecha_emision = Column(Date, nullable=True, index=True)
    # Indexado: alimenta el filtro por año y el informe de volumen anual.
    titulo = Column(String(500), nullable=True)  # nullable para borrador
    resumen = Column(Text, nullable=True)  # obligatorio al enviar, nullable para borrador
    palabras_clave = Column(JSON, nullable=True)  # lista de strings, max 5
    ambito_aplicacion = Column(String(30), nullable=True)
    # Opciones: local, provincial, nacional, internacional
    archivo_pdf_path = Column(String(500), nullable=True)  # obligatorio al enviar
    # Adjunto obligatorio. Se guarda solo el path: la subida la resuelve
    # upload_routes, este módulo nunca recibe el binario.

    # === 2. VIGENCIA Y CUMPLIMIENTO ===
    fecha_inicio_vigencia = Column(Date, nullable=True)
    fecha_expiracion = Column(Date, nullable=True)
    condiciones_finalizacion = Column(JSON, nullable=True)
    # Selección múltiple -> lista de strings. Valores esperados:
    # ["aprobacion_rendicion_cuentas", "certificado_libre_deuda", "otro"]
    otra_condicion_finalizacion = Column(String(255), nullable=True)

    # === 3. TEMATIZACIÓN DEL CONTENIDO JURÍDICO ===
    areas_vinculadas = Column(JSON, nullable=True)
    # Selección múltiple -> lista de strings. Valores esperados:
    # ["gerencia_fomento", "gerencia_exhibicion", "gerencia_capacitacion",
    #  "agam", "repa", "juridico", "consejo_directivo", "administracion_general",
    #  "produccion_comunitaria", "comision_filmaciones", "cinemateca"]
    # Va como JSON y no como tabla puente porque es un catálogo cerrado y chico
    # que solo se usa para filtrar; es el patrón de listas del repo.
    tematica_principal = Column(String(50), nullable=True, index=True)
    # Opciones: fomento_financiamiento, regulacion_normativa,
    # convenios_cooperacion, politicas_comunitarias,
    # regulacion_laboral_derechos_autor, lineamientos_institucionales, otro
    otra_tematica = Column(String(100), nullable=True)
    vinculado_resolucion_previa = Column(Boolean, nullable=False, default=False)
    resolucion_previa_id = Column(String(100), nullable=True, index=True)
    # Vínculo SIMPLE por número/ID, no FK a sí misma: el digesto se carga
    # retroactivamente y casi siempre la resolución previa todavía no existe
    # como fila. Una FK dura impediría cargar el instrumento nuevo.

    # === 5. VINCULACIÓN INSTITUCIONAL Y PUBLICIDAD ===
    codigo_repa_vinculado = Column(String(50), nullable=True, index=True)
    vinculado_proyecto = Column(String(20), nullable=True)  # si, no, evaluar
    proyecto_id = Column(String(100), nullable=True, index=True)
    # Mismo criterio que resolucion_previa_id: referencia textual al ID de
    # proyecto de Fomento, sin FK, para no acoplar el digesto a ese módulo.
    area_responsable_seguimiento = Column(String(200), nullable=True)
    requiere_publicacion = Column(String(20), nullable=True)  # si, no, parcial
    notas_internas = Column(Text, nullable=True)

    # === 6. OBSERVACIONES ===
    observaciones_adicionales = Column(Text, nullable=True)

    # === 7. CAMPOS AUTOMÁTICOS DEL SISTEMA ===
    usuario_carga_id = Column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    # Borrador: la fila existe pero todavia no se declara cargada. Mismo
    # patron que rodajes y los formularios del Padron.
    borrador = Column(Boolean, nullable=False, default=False)
    estado_revision = Column(String(20), nullable=False, default="en_revision")
    # Opciones: en_revision, validado, archivado
    # El "historial de modificaciones" del formulario no tiene tabla propia:
    # lo cubre el audit_log del proyecto (resource_type="InstrumentoJuridico").
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones
    usuario_carga = relationship("User")
    acta = relationship(
        "ActaConsejoDirectivo",
        back_populates="instrumento",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ActaConsejoDirectivo(Base):
    """
    Bloque condicional de la sección 4, visible solo cuando el tipo de documento
    es 'acta_consejo_directivo'.

    Va en tabla aparte (1:1 opcional) y no como columnas nullable sueltas en
    instrumentos_juridicos porque aplica a una minoría de las filas y porque el
    doc pide que las actas "se integren en una base específica".
    """

    __tablename__ = "actas_consejo_directivo"

    id = Column(Integer, primary_key=True, index=True)
    instrumento_id = Column(
        Integer,
        ForeignKey("instrumentos_juridicos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # unique = relación 1:1 con el instrumento
        index=True,
    )

    fecha_reunion = Column(Date, nullable=True)
    asistentes = Column(JSON, nullable=True)
    # Lista de objetos: {nombre, cargo, organizacion}
    ordenes_del_dia = Column(Text, nullable=True)
    decisiones_tomadas = Column(Text, nullable=True)
    acta_pdf_path = Column(String(500), nullable=True)
    resoluciones_emitidas = Column(JSON, nullable=True)
    # Lista de strings con los números de resolución emitidos en la reunión
    # (vinculación por número, mismo criterio que resolucion_previa_id).

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    instrumento = relationship("InstrumentoJuridico", back_populates="acta")
