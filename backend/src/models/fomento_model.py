# models/fomento_model.py
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.database import Base


class TramiteFomento(Base):
    """
    Modelo para Trámites de Fomento.
    Registra proyectos presentados a convocatorias, ventanilla continua, cash rebate, etc.
    """

    __tablename__ = "tramites_fomento"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # === IDENTIFICACIÓN ===
    tipo_tramite = Column(String(50), nullable=True)
    # Opciones: convocatoria_competitiva, ventanilla_continua, cash_rebate, semillero, convocatoria_especial

    # === EVENTO/LÍNEA/COHORTE ===
    evento_id = Column(Integer, nullable=True)  # Para convocatorias
    linea_id = Column(Integer, nullable=True)  # Para convocatorias
    cohorte_semillero_id = Column(Integer, nullable=True)  # Para semillero

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
    otros_aportes_no_iaavim = Column(
        JSON, nullable=True
    )  # Lista de {organismo, programa, monto, moneda}
    aportes_en_especie = Column(Text, nullable=True)

    # === ADJUNTOS ===
    carpeta_dossier_path = Column(String(500), nullable=True)
    presupuesto_detallado_path = Column(String(500), nullable=True)
    plan_financiamiento_path = Column(String(500), nullable=True)
    anexos_tecnicos_path = Column(String(500), nullable=True)

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
    pagos = Column(
        JSON, nullable=True
    )  # Lista de {fecha, monto, moneda, concepto, comprobante}
    rendicion_estado = Column(
        String(50), nullable=True
    )  # pendiente, presentada, observada, aprobada

    # AGAM
    estado_agam = Column(String(50), nullable=True)  # pendiente, recibido, ingresado
    fecha_entrega_copia = Column(DateTime, nullable=True)
    acta_recepcion_path = Column(String(500), nullable=True)

    # === ESTADO ===
    borrador = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relación con usuario
    user = relationship("User", back_populates="tramites_fomento")


class Evaluador(Base):
    """
    Modelo para Evaluadores y Jurados de procesos de fomento.
    """

    __tablename__ = "evaluadores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # === DATOS PERSONALES ===
    nombre_completo = Column(String(255), nullable=True)
    dni = Column(String(20), nullable=True)
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
