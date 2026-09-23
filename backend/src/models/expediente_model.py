# models/expediente_model.py
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from src.database import Base


class ExpedienteAdministrativo(Base):
    """
    Expediente administrativo del área de Administración General (IAAviM).

    Consolida la ejecución presupuestaria: expediente, montos, resolución
    asociada y estado de pago. Es un registro de uso interno del área (no lo
    carga el ciudadano), por eso no tiene user_id propietario ni lifecycle
    de aprobación como los formularios del padrón.
    """

    __tablename__ = "expedientes_administrativos"
    __table_args__ = (
        CheckConstraint(
            "tipo_expediente IN ('apoyo_directo', 'subsidio_convocatoria', "
            "'pago_capacitadores', 'contratacion_servicio', "
            "'convenio_terceros', 'otro')",
            name="ck_expedientes_administrativos_tipo_expediente",
        ),
        CheckConstraint(
            "area_solicitante IN ('fomento', 'capacitacion', "
            "'exhibicion_distribucion', 'agam', 'repa', 'cinemateca', "
            "'comunicacion', 'juridico', 'comision_filmaciones', "
            "'consejo_directivo', 'presidencia')",
            name="ck_expedientes_administrativos_area_solicitante",
        ),
        CheckConstraint(
            "estado_expediente IN ('iniciado', 'en_proceso_administrativo', "
            "'en_tesoreria', 'aprobado_para_pago', 'pagado', "
            "'observado_rechazado')",
            name="ck_expedientes_administrativos_estado_expediente",
        ),
        CheckConstraint(
            "fuente_presupuestaria IN ('presupuesto_iaavim', "
            "'convenio_externo', 'cofinanciado')",
            name="ck_expedientes_administrativos_fuente_presupuestaria",
        ),
        CheckConstraint(
            "forma_pago IN ('transferencia', 'orden_compra', 'otro')",
            name="ck_expedientes_administrativos_forma_pago",
        ),
    )

    # El identificador del expediente es este `id` incremental propio: en esta
    # version NO se integra con el sistema provincial (decision del PM).
    id = Column(Integer, primary_key=True, index=True)

    # === DATOS GENERALES DEL EXPEDIENTE ===
    # Campo libre para transcribir a mano el numero que asigna la provincia
    # cuando se conozca; no se valida ni se usa como clave.
    numero_expediente_provincial = Column(String(100), nullable=True, index=True)
    fecha_alta = Column(Date, nullable=True, index=True)

    tipo_expediente = Column(String(50), nullable=True, index=True)
    # Opciones: apoyo_directo, subsidio_convocatoria, pago_capacitadores,
    # contratacion_servicio, convenio_terceros, otro
    otro_tipo = Column(String(255), nullable=True)  # detalle cuando tipo = otro

    area_solicitante = Column(String(50), nullable=True, index=True)
    # Opciones: fomento, capacitacion, exhibicion_distribucion, agam, repa,
    # cinemateca, comunicacion, juridico, comision_filmaciones,
    # consejo_directivo, presidencia

    nombre_proyecto = Column(String(255), nullable=True)
    # Codigo RePA del beneficiario. Se guarda como texto y no como FK porque el
    # codigo puede apuntar a PF, PJ, asociacion o ESA (tablas distintas) y el
    # expediente tambien existe para gastos sin beneficiario inscripto.
    codigo_repa = Column(String(50), nullable=True, index=True)

    # === RESOLUCION ASOCIADA ===
    # El ID viaja como texto porque las resoluciones se numeran "NNN/AAAA".
    resolucion_id = Column(String(100), nullable=True)
    # El PDF lo sube el frontend por /upload/document/{doc_type}; aca solo se
    # guarda el path que devuelve ese endpoint.
    resolucion_pdf_path = Column(String(500), nullable=True)

    estado_expediente = Column(String(50), nullable=True, index=True)
    # Opciones: iniciado, en_proceso_administrativo, en_tesoreria,
    # aprobado_para_pago, pagado, observado_rechazado

    # === EJECUCION PRESUPUESTARIA ===
    # Numeric y no Float: son importes en pesos que despues se suman para los
    # indicadores; el redondeo binario de Float desvirtua los totales.
    monto_solicitado = Column(Numeric(14, 2), nullable=True)
    monto_aprobado = Column(Numeric(14, 2), nullable=True)
    monto_ejecutado = Column(Numeric(14, 2), nullable=True)

    fuente_presupuestaria = Column(String(50), nullable=True, index=True)
    # Opciones: presupuesto_iaavim, convenio_externo, cofinanciado
    fecha_pago_final = Column(Date, nullable=True)
    forma_pago = Column(String(30), nullable=True)
    # Opciones: transferencia, orden_compra, otro

    # === SEGUIMIENTO Y OBSERVACIONES ===
    # Tri-estado (si / no / en evaluacion), por eso String y no Boolean.
    genera_informe_financiero = Column(String(20), nullable=True)
    # Opciones: si, no, en_evaluacion
    genera_devolucion = Column(Boolean, nullable=True)
    observaciones_administrativas = Column(Text, nullable=True)

    # === METADATOS ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
