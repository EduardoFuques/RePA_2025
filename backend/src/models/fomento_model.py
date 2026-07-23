# models/fomento_model.py
from datetime import datetime, timezone

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
from sqlalchemy.orm import relationship

from src.database import Base

# === CATÁLOGOS: EVENTOS Y LÍNEAS ===


class EventoFomento(Base):
    """
    Evento / Convocatoria de Fomento.
    Estructura madre que agrupa líneas, proyectos y evaluaciones.
    """

    __tablename__ = "eventos_fomento"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    anio_edicion = Column(Integer, nullable=False)
    tipo = Column(String(50), nullable=False)  # competitiva, especial
    estado = Column(String(30), nullable=False, default="borrador")
    # borrador, activo, cerrado
    fecha_apertura = Column(DateTime, nullable=True)
    fecha_cierre = Column(DateTime, nullable=True)
    bases_condiciones_path = Column(String(500), nullable=True)
    presupuesto_global = Column(Integer, nullable=True)
    observaciones = Column(Text, nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    lineas = relationship(
        "LineaFomento", back_populates="evento", cascade="all, delete-orphan"
    )


class LineaFomento(Base):
    """
    Línea de fomento dentro de un evento/convocatoria.
    Define requisitos, topes y campos específicos.
    """

    __tablename__ = "lineas_fomento"

    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos_fomento.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    vigente = Column(Boolean, default=True, nullable=False)
    tope_por_proyecto = Column(Integer, nullable=True)
    moneda_tope = Column(String(10), nullable=True)  # ARS, USD
    cupo = Column(Integer, nullable=True)
    requiere_evaluacion = Column(Boolean, default=True)
    tipo_comite = Column(String(50), nullable=True)  # tecnico, deliberativo
    documentacion_requerida = Column(JSON, nullable=True)  # checklist
    campos_especificos = Column(JSON, nullable=True)
    # Lista de {etiqueta, tipo_dato, obligatorio, ayuda, orden}
    observaciones = Column(Text, nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    evento = relationship("EventoFomento", back_populates="lineas")


# === TRÁMITES Y EVALUADORES ===


class TramiteFomento(Base):
    """
    Modelo para Trámites de Fomento.
    Registra proyectos presentados a convocatorias, ventanilla continua, cash rebate, etc.
    """

    __tablename__ = "tramites_fomento"
    __table_args__ = (
        CheckConstraint(
            "tipo_tramite IN ('convocatoria_competitiva', 'ventanilla_continua', "
            "'cash_rebate', 'semillero', 'convocatoria_especial')",
            name="ck_tramites_fomento_tipo_tramite",
        ),
        CheckConstraint(
            "tipo_productora IN ('productora_asociada', 'coproductora_misionera', "
            "'productora_misionera', 'otra')",
            name="ck_tramites_fomento_tipo_productora",
        ),
        CheckConstraint(
            "medio IN ('cine', 'tv', 'web', 'videojuego')",
            name="ck_tramites_fomento_medio",
        ),
        CheckConstraint(
            "genero IN ('ficcion', 'documental', 'animacion', 'experimental')",
            name="ck_tramites_fomento_genero",
        ),
        CheckConstraint(
            "extension IN ('corto', 'largo')",
            name="ck_tramites_fomento_extension",
        ),
        CheckConstraint(
            "formato_narrativo IN ('unitario', 'serie')",
            name="ck_tramites_fomento_formato_narrativo",
        ),
        CheckConstraint(
            # Unión de los 4 sub-flujos que comparten esta columna (Convocatoria /
            # Ventanilla / Cash Rebate / Semillero).
            "estado_tramite IN ('presentado', 'admisible', 'evaluado', 'seleccionado', "
            "'no_seleccionado', 'desistido', 'retirado', 'ingresado', 'en_evaluacion', "
            "'aprobado', 'denegado', 'verificacion', 'convenio', 'liquidado', "
            "'inscripto', 'en_curso', 'finalizado')",
            name="ck_tramites_fomento_estado_tramite",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # === IDENTIFICACIÓN ===
    tipo_tramite = Column(String(50), nullable=True)
    # Opciones: convocatoria_competitiva, ventanilla_continua, cash_rebate, semillero, convocatoria_especial

    # === EVENTO/LÍNEA/COHORTE ===
    # FK reales (antes Integer suelto sin constraint — permitía referencias
    # colgadas a un evento/línea/cohorte borrado o inexistente).
    evento_id = Column(
        Integer, ForeignKey("eventos_fomento.id"), nullable=True
    )  # Para convocatorias
    linea_id = Column(
        Integer, ForeignKey("lineas_fomento.id"), nullable=True
    )  # Para convocatorias
    cohorte_semillero_id = Column(
        Integer, ForeignKey("cohortes_semillero.id"), nullable=True
    )  # Para semillero

    # === PRESENTANTE ===
    codigo_repa_presentante = Column(String(50), nullable=True)
    tipo_productora = Column(String(50), nullable=True)
    # Opciones: productora_asociada, coproductora_misionera, productora_misionera, otra
    distrito_presentante = Column(String(50), nullable=True)
    contacto_email = Column(String(255), nullable=True)
    contacto_telefono = Column(String(30), nullable=True)

    # === DATOS DEL PROYECTO ===
    titulo_proyecto = Column(String(255), nullable=True)
    medio = Column(String(50), nullable=True)
    # Opciones: cine, tv, web, videojuego
    genero = Column(String(50), nullable=True)
    # Opciones: ficcion, documental, animacion, experimental
    extension = Column(String(30), nullable=True)
    # Opciones: corto, largo
    formato_narrativo = Column(String(30), nullable=True)
    # Opciones: unitario, serie
    duracion_estimada_min = Column(Integer, nullable=True)
    sinopsis = Column(Text, nullable=True)
    subgenero = Column(String(100), nullable=True)
    etapa = Column(String(50), nullable=True)
    pais = Column(String(100), nullable=True)
    idioma_original = Column(String(50), nullable=True)

    # === PRESUPUESTO Y FINANCIAMIENTO ===
    moneda_principal = Column(String(10), nullable=True)  # ARS, USD
    presupuesto_total = Column(Integer, nullable=True)
    monto_solicitado_iaavim = Column(Integer, nullable=True)
    monto_aprobado_iaavim = Column(Integer, nullable=True)
    aporte_privado_monto = Column(Integer, nullable=True)
    aporte_privado_fuente = Column(String(255), nullable=True)
    # Relación 1:N — antes JSON suelto (ver AporteFomento más abajo). Se
    # sincroniza completo en cada guardado (reemplazar-todo), no incremental.
    aportes_rel = relationship(
        "AporteFomento", cascade="all, delete-orphan", back_populates="tramite"
    )
    aportes_en_especie = Column(Text, nullable=True)

    # === CASH REBATE ===
    monto_estimado_reintegro = Column(Integer, nullable=True)
    gastos_elegibles = Column(Text, nullable=True)
    montos_invertidos_provincia = Column(Integer, nullable=True)
    distritos_rodaje = Column(JSON, nullable=True)  # Lista de distritos
    fechas_rodaje = Column(JSON, nullable=True)  # {fecha_inicio, fecha_fin}
    postulante_linea_nacional = Column(String(255), nullable=True)
    postulante_linea_misionera = Column(String(255), nullable=True)

    # === ADJUNTOS ===
    carpeta_dossier_path = Column(String(500), nullable=True)
    presupuesto_detallado_path = Column(String(500), nullable=True)
    plan_financiamiento_path = Column(String(500), nullable=True)
    anexos_tecnicos_path = Column(String(500), nullable=True)

    # === OTROS DOCUMENTOS ===
    otros_documentos = Column(JSON, nullable=True)  # Lista de {tipo, descripcion, path}

    # === ESTADO Y FECHAS ===
    estado_tramite = Column(String(50), nullable=True)
    # Convocatoria: presentado, admisible, evaluado, seleccionado, no_seleccionado, desistido, retirado
    # Ventanilla: ingresado, en_evaluacion, aprobado, denegado
    # Cash Rebate: ingresado, verificacion, aprobado, convenio, liquidado
    # Semillero: inscripto, seleccionado, en_curso, finalizado
    fecha_ingreso = Column(
        DateTime, nullable=True, default=lambda: datetime.now(timezone.utc)
    )
    fecha_dictamen = Column(DateTime, nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    fecha_cierre = Column(DateTime, nullable=True)

    # === VINCULACIONES INTERÁREA ===
    pendiente_juridico = Column(Boolean, default=False)
    motivo_juridico = Column(String(255), nullable=True)
    fecha_pendiente_juridico = Column(DateTime, nullable=True)

    pendiente_administracion = Column(Boolean, default=False)
    motivo_administracion = Column(String(255), nullable=True)
    fecha_pendiente_administracion = Column(DateTime, nullable=True)

    pendiente_agam = Column(Boolean, default=False)
    motivo_agam = Column(String(255), nullable=True)
    fecha_pendiente_agam = Column(DateTime, nullable=True)

    # === SECCIONES CONDICIONALES ===
    # Evaluación
    comite_asignado_id = Column(Integer, nullable=True)

    # Jurídico
    resolucion_otorgamiento_id = Column(Integer, nullable=True)
    resolucion_otorgamiento_path = Column(String(500), nullable=True)
    convenio_path = Column(String(500), nullable=True)

    # Administración
    nro_expediente = Column(String(50), nullable=True)
    # Relación 1:N — antes JSON suelto (ver PagoFomento más abajo). Se
    # sincroniza completo en cada guardado (reemplazar-todo), no incremental.
    pagos_rel = relationship(
        "PagoFomento", cascade="all, delete-orphan", back_populates="tramite"
    )
    rendicion_estado = Column(
        String(50), nullable=True
    )  # pendiente, presentada, observada, aprobada

    # AGAM
    estado_agam = Column(String(50), nullable=True)  # pendiente, recibido, ingresado
    fecha_entrega_copia = Column(DateTime, nullable=True)
    acta_recepcion_path = Column(String(500), nullable=True)

    # === ESTADO ===
    borrador = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relación con usuario
    user = relationship("User", back_populates="tramites_fomento")


# === COMITÉS Y DICTÁMENES ===


class ComiteFomento(Base):
    """
    Modelo para Comités de evaluación de fomento.
    Agrupan evaluadores asignados a un evento/línea para emitir dictámenes.
    """

    __tablename__ = "comites_fomento"

    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos_fomento.id"), nullable=False)
    linea_id = Column(Integer, ForeignKey("lineas_fomento.id"), nullable=True)
    tipo = Column(String(50), nullable=False)  # tecnico, deliberativo
    nombre = Column(String(255), nullable=True)
    # Relación 1:N — antes JSON suelto (ver IntegranteComite más abajo). Se
    # sincroniza completo en cada guardado (reemplazar-todo), no incremental.
    integrantes_rel = relationship(
        "IntegranteComite", cascade="all, delete-orphan", back_populates="comite"
    )
    resolucion_designacion_path = Column(String(500), nullable=True)
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    evento = relationship("EventoFomento")
    linea = relationship("LineaFomento")
    dictamenes = relationship(
        "DictamenFomento", back_populates="comite", cascade="all, delete-orphan"
    )


class DictamenFomento(Base):
    """
    Modelo para Dictámenes emitidos por evaluadores sobre trámites de fomento.
    """

    __tablename__ = "dictamenes_fomento"

    id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(Integer, ForeignKey("tramites_fomento.id"), nullable=False)
    comite_id = Column(Integer, ForeignKey("comites_fomento.id"), nullable=True)
    evaluador_id = Column(Integer, ForeignKey("evaluadores.id"), nullable=False)
    tipo_dictamen = Column(
        String(50), nullable=False
    )  # tecnico, deliberativo, consultoria
    fecha = Column(DateTime, nullable=True)
    observaciones = Column(Text, nullable=True)
    puntaje = Column(Integer, nullable=True)
    archivo_pdf_path = Column(String(500), nullable=True)
    devolucion_presentante = Column(Boolean, default=False)
    devolucion_archivo_path = Column(String(500), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tramite = relationship("TramiteFomento")
    comite = relationship("ComiteFomento", back_populates="dictamenes")
    evaluador = relationship("Evaluador")


class Evaluador(Base):
    """
    Modelo para Evaluadores y Jurados de procesos de fomento.
    """

    __tablename__ = "evaluadores"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('evaluador_tecnico', 'jurado_deliberativo', 'consultor')",
            name="ck_evaluadores_rol",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # === DATOS PERSONALES ===
    nombre_completo = Column(String(255), nullable=True)
    dni = Column(String(20), unique=True, nullable=True)
    email = Column(String(255), nullable=True)
    telefono = Column(String(30), nullable=True)
    localidad = Column(String(100), nullable=True)
    provincia_pais = Column(String(100), nullable=True)
    vinculo_repa = Column(String(100), nullable=True)

    # === FORMACIÓN Y EXPERIENCIA ===
    formacion_academica = Column(Text, nullable=True)
    experiencia_audiovisual = Column(Text, nullable=True)
    areas_especializacion = Column(JSON, nullable=True)  # Lista de áreas
    otra_area_especializacion = Column(String(255), nullable=True)
    participacion_jurados = Column(Text, nullable=True)
    cv_path = Column(String(500), nullable=True)
    especialidades = Column(JSON, nullable=True)  # Lista de especialidades

    # === ROLES Y PARTICIPACIÓN ===
    roles_habilitados = Column(
        JSON, nullable=True
    )  # técnico, deliberativo, consultoría
    edicion_linea_evaluada = Column(String(255), nullable=True)
    rol = Column(String(50), nullable=True)
    # Opciones: evaluador_tecnico, jurado_deliberativo, consultor

    # === DISPONIBILIDAD ===
    disponible_convocatorias = Column(Boolean, default=True)
    tipos_convocatoria = Column(JSON, nullable=True)  # Lista de tipos
    horas_semanales = Column(String(20), nullable=True)
    modalidad_preferida = Column(String(50), nullable=True)

    # === PARTICIPACIÓN ===
    emitio_dictamen = Column(Boolean, default=False)
    resolucion_designacion_path = Column(String(500), nullable=True)

    # === CONTACTO Y OBSERVACIONES ===
    contacto = Column(String(255), nullable=True)
    observaciones = Column(Text, nullable=True)

    # === ESTADO ===
    borrador = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relación con usuario
    user = relationship("User", back_populates="evaluadores")


# === SEMILLERO DE PRODUCTORES ===


class CohorteSemillero(Base):
    """
    Modelo para Cohortes del Semillero de Productores.
    Cada cohorte agrupa participantes en un período determinado.
    """

    __tablename__ = "cohortes_semillero"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    anio_edicion = Column(Integer, nullable=False)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    descripcion = Column(Text, nullable=True)
    cupo = Column(Integer, nullable=True)
    estado = Column(String(50), nullable=False, default="planificada")
    # planificada, inscripcion_abierta, en_curso, finalizada
    observaciones = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    participantes = relationship(
        "ParticipanteSemillero",
        back_populates="cohorte",
        cascade="all, delete-orphan",
    )


class ParticipanteSemillero(Base):
    """
    Modelo para Participantes del Semillero.
    Vincula un código RePA a una cohorte con diagnóstico y objetivos.
    """

    __tablename__ = "participantes_semillero"

    id = Column(Integer, primary_key=True, index=True)
    cohorte_id = Column(Integer, ForeignKey("cohortes_semillero.id"), nullable=False)
    codigo_repa = Column(String(50), nullable=True)
    nombre_completo = Column(String(255), nullable=True)
    distrito = Column(String(100), nullable=True)
    tramites_vinculados = Column(JSON, nullable=True)  # Lista de IDs de trámites
    formacion_previa = Column(Text, nullable=True)
    proyectos_en_desarrollo = Column(Text, nullable=True)
    participacion_capacitaciones_iaavim = Column(String(20), nullable=True)  # si, no
    diagnostico_inicial = Column(Text, nullable=True)
    objetivos = Column(Text, nullable=True)

    # Cierre
    estado = Column(String(50), nullable=False, default="activo")
    # activo, egresado, abandono, continua
    resultados_cualitativos = Column(Text, nullable=True)
    resultados_cuantificables = Column(JSON, nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cohorte = relationship("CohorteSemillero", back_populates="participantes")
    acompanamientos = relationship(
        "AcompanamientoSemillero",
        back_populates="participante",
        cascade="all, delete-orphan",
    )


class AcompanamientoSemillero(Base):
    """
    Modelo para Acompañamientos dentro del Semillero.
    Registra actividades de tutoría, clínica, pitch, etc.
    """

    __tablename__ = "acompanamientos_semillero"

    id = Column(Integer, primary_key=True, index=True)
    participante_id = Column(
        Integer, ForeignKey("participantes_semillero.id"), nullable=False
    )
    tipo = Column(String(50), nullable=False)
    # tutoria, desarrollo_carpeta, clinica, pitch, asesoria, otros
    fecha = Column(DateTime, nullable=True)
    responsable = Column(String(255), nullable=True)
    observaciones = Column(Text, nullable=True)
    adjuntos = Column(JSON, nullable=True)  # Lista de {nombre, path}
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    participante = relationship(
        "ParticipanteSemillero", back_populates="acompanamientos"
    )


# === PAGOS, APORTES E INTEGRANTES DE COMITÉ (antes JSON suelto) ===


class PagoFomento(Base):
    """
    Pago administrativo de un trámite de fomento (rendición).
    Antes vivía como `TramiteFomento.pagos` (JSON sin validar); se
    sincroniza completo en cada guardado admin (reemplazar-todo), no
    incremental — ver `services/fomento_relational_service.sync_pagos`.
    """

    __tablename__ = "pagos_fomento"

    id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(
        Integer,
        ForeignKey("tramites_fomento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha = Column(DateTime, nullable=True)
    monto = Column(Integer, nullable=True)
    moneda = Column(String(10), nullable=True)
    concepto = Column(String(255), nullable=True)
    comprobante = Column(
        String(500), nullable=True
    )  # sin UI de upload aún — texto/path plano
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    tramite = relationship("TramiteFomento", back_populates="pagos_rel")


class AporteFomento(Base):
    """
    Aporte no-IAAviM declarado por el solicitante de un trámite de fomento.
    Antes vivía como `TramiteFomento.otros_aportes_no_iaavim` (JSON sin
    validar); se sincroniza completo en cada guardado (reemplazar-todo) —
    ver `services/fomento_relational_service.sync_aportes`.
    """

    __tablename__ = "aportes_fomento"

    id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(
        Integer,
        ForeignKey("tramites_fomento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organismo = Column(String(255), nullable=True)
    programa = Column(String(255), nullable=True)
    monto = Column(Integer, nullable=True)
    moneda = Column(String(10), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    tramite = relationship("TramiteFomento", back_populates="aportes_rel")


class IntegranteComite(Base):
    """
    Integrante (evaluador) de un comité de fomento.
    Antes vivía como `ComiteFomento.integrantes` (JSON sin validar, sin FK a
    `evaluadores` — un evaluador_id inexistente pasaba sin error); ahora es
    una FK real, validada antes de aplicar el lote — ver
    `services/fomento_relational_service.sync_integrantes`.
    """

    __tablename__ = "integrantes_comite"

    id = Column(Integer, primary_key=True, index=True)
    comite_id = Column(
        Integer,
        ForeignKey("comites_fomento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Sin ondelete: si el evaluador se borra, se prefiere que falle antes que
    # borrar en silencio la membresía histórica del comité (mismo criterio
    # que DictamenFomento.evaluador_id, arriba).
    evaluador_id = Column(
        Integer, ForeignKey("evaluadores.id"), nullable=False, index=True
    )
    rol = Column(String(50), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    comite = relationship("ComiteFomento", back_populates="integrantes_rel")
    evaluador = relationship("Evaluador")
