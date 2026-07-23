# schemas/fomento_schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# === ÍTEMS DE LAS RELACIONES 1:N (antes JSON suelto en TramiteFomento/ComiteFomento) ===


class PagoItem(BaseModel):
    """Un pago de rendición de un trámite de fomento (solo-admin)."""

    fecha: datetime | None = None
    monto: int | None = None
    moneda: str | None = Field(None, max_length=10)
    concepto: str | None = Field(None, max_length=255)
    comprobante: str | None = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class AporteItem(BaseModel):
    """Un aporte no-IAAviM declarado por el solicitante."""

    organismo: str | None = Field(None, max_length=255)
    programa: str | None = Field(None, max_length=255)
    monto: int | None = None
    moneda: str | None = Field(None, max_length=10)

    model_config = ConfigDict(from_attributes=True)


class IntegranteItem(BaseModel):
    """Un integrante (evaluador) de un comité de fomento."""

    evaluador_id: int
    rol: str | None = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


# === EVENTO DE FOMENTO ===


class EventoFomentoCreate(BaseModel):
    """Schema para crear un Evento/Convocatoria de Fomento"""

    nombre: str = Field(..., max_length=255)
    anio_edicion: int
    tipo: str = Field(..., max_length=50)
    estado: str = Field(default="borrador", max_length=30)
    fecha_apertura: datetime | None = None
    fecha_cierre: datetime | None = None
    bases_condiciones_path: str | None = Field(None, max_length=500)
    presupuesto_global: int | None = None
    observaciones: str | None = None


class EventoFomentoUpdate(BaseModel):
    """Schema para actualizar un Evento/Convocatoria"""

    nombre: str | None = Field(None, max_length=255)
    anio_edicion: int | None = None
    tipo: str | None = Field(None, max_length=50)
    estado: str | None = Field(None, max_length=30)
    fecha_apertura: datetime | None = None
    fecha_cierre: datetime | None = None
    bases_condiciones_path: str | None = Field(None, max_length=500)
    presupuesto_global: int | None = None
    observaciones: str | None = None


class LineaFomentoOut(BaseModel):
    """Schema de salida para Línea (embebido en EventoOut)"""

    id: int
    evento_id: int
    nombre: str
    vigente: bool
    tope_por_proyecto: int | None = None
    moneda_tope: str | None = None
    cupo: int | None = None
    requiere_evaluacion: bool
    tipo_comite: str | None = None
    documentacion_requerida: list[dict] | None = None
    campos_especificos: list[dict] | None = None
    observaciones: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EventoFomentoOut(BaseModel):
    """Schema de salida para Evento/Convocatoria"""

    id: int
    nombre: str
    anio_edicion: int
    tipo: str
    estado: str
    fecha_apertura: datetime | None = None
    fecha_cierre: datetime | None = None
    bases_condiciones_path: str | None = None
    presupuesto_global: int | None = None
    observaciones: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    lineas: list[LineaFomentoOut] = []

    model_config = ConfigDict(from_attributes=True)


# === LÍNEA DE FOMENTO ===


class LineaFomentoCreate(BaseModel):
    """Schema para crear una Línea de Fomento"""

    nombre: str = Field(..., max_length=255)
    vigente: bool = True
    tope_por_proyecto: int | None = None
    moneda_tope: str | None = Field(None, max_length=10)
    cupo: int | None = None
    requiere_evaluacion: bool = True
    tipo_comite: str | None = Field(None, max_length=50)
    documentacion_requerida: list[dict] | None = None
    campos_especificos: list[dict] | None = None
    observaciones: str | None = None


class LineaFomentoUpdate(BaseModel):
    """Schema para actualizar una Línea"""

    nombre: str | None = Field(None, max_length=255)
    vigente: bool | None = None
    tope_por_proyecto: int | None = None
    moneda_tope: str | None = Field(None, max_length=10)
    cupo: int | None = None
    requiere_evaluacion: bool | None = None
    tipo_comite: str | None = Field(None, max_length=50)
    documentacion_requerida: list[dict] | None = None
    campos_especificos: list[dict] | None = None
    observaciones: str | None = None


# === COMITÉ DE FOMENTO ===


class ComiteFomentoCreate(BaseModel):
    """Schema para crear un Comité de evaluación"""

    evento_id: int
    linea_id: int | None = None
    tipo: str = Field(..., max_length=50)  # tecnico, deliberativo
    nombre: str | None = Field(None, max_length=255)
    integrantes: list[IntegranteItem] | None = None
    resolucion_designacion_path: str | None = Field(None, max_length=500)
    observaciones: str | None = None
    activo: bool = True


class ComiteFomentoUpdate(BaseModel):
    """Schema para actualizar un Comité"""

    linea_id: int | None = None
    tipo: str | None = Field(None, max_length=50)
    nombre: str | None = Field(None, max_length=255)
    integrantes: list[IntegranteItem] | None = None
    resolucion_designacion_path: str | None = Field(None, max_length=500)
    observaciones: str | None = None
    activo: bool | None = None


class ComiteFomentoOut(BaseModel):
    """Schema de salida para Comité"""

    id: int
    evento_id: int
    linea_id: int | None = None
    tipo: str
    nombre: str | None = None
    integrantes: list[IntegranteItem] | None = None
    resolucion_designacion_path: str | None = None
    observaciones: str | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === DICTAMEN DE FOMENTO ===


class DictamenFomentoCreate(BaseModel):
    """Schema para crear un Dictamen"""

    tramite_id: int
    comite_id: int | None = None
    evaluador_id: int
    tipo_dictamen: str = Field(..., max_length=50)  # tecnico, deliberativo, consultoria
    fecha: datetime | None = None
    observaciones: str | None = None
    puntaje: int | None = None
    archivo_pdf_path: str | None = Field(None, max_length=500)
    devolucion_presentante: bool = False
    devolucion_archivo_path: str | None = Field(None, max_length=500)


class DictamenFomentoUpdate(BaseModel):
    """Schema para actualizar un Dictamen"""

    comite_id: int | None = None
    tipo_dictamen: str | None = Field(None, max_length=50)
    fecha: datetime | None = None
    observaciones: str | None = None
    puntaje: int | None = None
    archivo_pdf_path: str | None = Field(None, max_length=500)
    devolucion_presentante: bool | None = None
    devolucion_archivo_path: str | None = Field(None, max_length=500)


class DictamenFomentoOut(BaseModel):
    """Schema de salida para Dictamen"""

    id: int
    tramite_id: int
    comite_id: int | None = None
    evaluador_id: int
    tipo_dictamen: str
    fecha: datetime | None = None
    observaciones: str | None = None
    puntaje: int | None = None
    archivo_pdf_path: str | None = None
    devolucion_presentante: bool
    devolucion_archivo_path: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === TRÁMITE DE FOMENTO ===


class TramiteFomentoCreate(BaseModel):
    """Schema para crear un Trámite de Fomento"""

    tipo_tramite: str | None = Field(None, max_length=50)
    evento_id: int | None = None
    linea_id: int | None = None
    cohorte_semillero_id: int | None = None

    codigo_repa_presentante: str | None = Field(None, max_length=50)
    tipo_productora: str | None = Field(None, max_length=50)
    distrito_presentante: str | None = Field(None, max_length=50)
    contacto_email: str | None = Field(None, max_length=255)
    contacto_telefono: str | None = Field(None, max_length=30)

    titulo_proyecto: str | None = Field(None, max_length=255)
    medio: str | None = Field(None, max_length=50)
    genero: str | None = Field(None, max_length=50)
    extension: str | None = Field(None, max_length=30)
    formato_narrativo: str | None = Field(None, max_length=30)
    duracion_estimada_min: int | None = None
    sinopsis: str | None = None
    subgenero: str | None = Field(None, max_length=100)
    etapa: str | None = Field(None, max_length=50)
    pais: str | None = Field(None, max_length=100)
    idioma_original: str | None = Field(None, max_length=50)

    moneda_principal: str | None = Field(None, max_length=10)
    presupuesto_total: int | None = None
    monto_solicitado_iaavim: int | None = None
    aporte_privado_monto: int | None = None
    aporte_privado_fuente: str | None = Field(None, max_length=255)
    otros_aportes_no_iaavim: list[AporteItem] | None = None
    aportes_en_especie: str | None = None

    monto_estimado_reintegro: int | None = None
    gastos_elegibles: str | None = None
    montos_invertidos_provincia: int | None = None
    distritos_rodaje: list[str] | None = None
    fechas_rodaje: dict | None = None
    postulante_linea_nacional: str | None = Field(None, max_length=255)
    postulante_linea_misionera: str | None = Field(None, max_length=255)

    carpeta_dossier_path: str | None = Field(None, max_length=500)
    presupuesto_detallado_path: str | None = Field(None, max_length=500)
    plan_financiamiento_path: str | None = Field(None, max_length=500)
    anexos_tecnicos_path: str | None = Field(None, max_length=500)
    otros_documentos: list[dict] | None = None

    # NOTA: los campos administrativos (estado_tramite, monto_aprobado_iaavim,
    # nro_expediente, resoluciones, pagos, vinculaciones interáreas, fechas de
    # dictamen/resolución/cierre, etc.) NO están acá a propósito: solo pueden
    # modificarse vía TramiteFomentoAdminUpdate en la ruta admin. Un
    # solicitante no debe poder autoaprobarse el subsidio ni fijarse el monto.

    borrador: bool = True


class TramiteFomentoUpdate(BaseModel):
    """Schema para actualizar un Trámite de Fomento"""

    tipo_tramite: str | None = Field(None, max_length=50)
    evento_id: int | None = None
    linea_id: int | None = None
    cohorte_semillero_id: int | None = None

    codigo_repa_presentante: str | None = Field(None, max_length=50)
    tipo_productora: str | None = Field(None, max_length=50)
    distrito_presentante: str | None = Field(None, max_length=50)
    contacto_email: str | None = Field(None, max_length=255)
    contacto_telefono: str | None = Field(None, max_length=30)

    titulo_proyecto: str | None = Field(None, max_length=255)
    medio: str | None = Field(None, max_length=50)
    genero: str | None = Field(None, max_length=50)
    extension: str | None = Field(None, max_length=30)
    formato_narrativo: str | None = Field(None, max_length=30)
    duracion_estimada_min: int | None = None
    sinopsis: str | None = None
    subgenero: str | None = Field(None, max_length=100)
    etapa: str | None = Field(None, max_length=50)
    pais: str | None = Field(None, max_length=100)
    idioma_original: str | None = Field(None, max_length=50)

    moneda_principal: str | None = Field(None, max_length=10)
    presupuesto_total: int | None = None
    monto_solicitado_iaavim: int | None = None
    aporte_privado_monto: int | None = None
    aporte_privado_fuente: str | None = Field(None, max_length=255)
    otros_aportes_no_iaavim: list[AporteItem] | None = None
    aportes_en_especie: str | None = None

    monto_estimado_reintegro: int | None = None
    gastos_elegibles: str | None = None
    montos_invertidos_provincia: int | None = None
    distritos_rodaje: list[str] | None = None
    fechas_rodaje: dict | None = None
    postulante_linea_nacional: str | None = Field(None, max_length=255)
    postulante_linea_misionera: str | None = Field(None, max_length=255)

    carpeta_dossier_path: str | None = Field(None, max_length=500)
    presupuesto_detallado_path: str | None = Field(None, max_length=500)
    plan_financiamiento_path: str | None = Field(None, max_length=500)
    anexos_tecnicos_path: str | None = Field(None, max_length=500)
    otros_documentos: list[dict] | None = None

    # NOTA: sin campos administrativos — ver nota en TramiteFomentoCreate.

    borrador: bool | None = None


class TramiteFomentoAdminUpdate(TramiteFomentoUpdate):
    """Schema para actualización ADMIN de un Trámite de Fomento.

    Extiende el schema de usuario con los campos administrativos del
    expediente (estado, montos aprobados, resoluciones, pagos, vinculaciones
    interáreas). Solo se usa en la ruta admin protegida por fomento:manage (check_permissions).
    """

    monto_aprobado_iaavim: int | None = None

    estado_tramite: str | None = Field(None, max_length=50)
    fecha_ingreso: datetime | None = None
    fecha_dictamen: datetime | None = None
    fecha_resolucion: datetime | None = None
    fecha_cierre: datetime | None = None

    pendiente_juridico: bool | None = None
    motivo_juridico: str | None = Field(None, max_length=255)
    fecha_pendiente_juridico: datetime | None = None
    pendiente_administracion: bool | None = None
    motivo_administracion: str | None = Field(None, max_length=255)
    fecha_pendiente_administracion: datetime | None = None
    pendiente_agam: bool | None = None
    motivo_agam: str | None = Field(None, max_length=255)
    fecha_pendiente_agam: datetime | None = None

    comite_asignado_id: int | None = None
    resolucion_otorgamiento_id: int | None = None
    resolucion_otorgamiento_path: str | None = Field(None, max_length=500)
    convenio_path: str | None = Field(None, max_length=500)

    nro_expediente: str | None = Field(None, max_length=50)
    pagos: list[PagoItem] | None = None
    rendicion_estado: str | None = Field(None, max_length=50)

    estado_agam: str | None = Field(None, max_length=50)
    fecha_entrega_copia: datetime | None = None
    acta_recepcion_path: str | None = Field(None, max_length=500)


class TramiteFomentoOut(BaseModel):
    """Schema de salida para Trámite de Fomento"""

    id: int
    user_id: str
    tipo_tramite: str | None = None
    evento_id: int | None = None
    linea_id: int | None = None
    cohorte_semillero_id: int | None = None

    codigo_repa_presentante: str | None = None
    tipo_productora: str | None = None
    distrito_presentante: str | None = None
    contacto_email: str | None = None
    contacto_telefono: str | None = None

    titulo_proyecto: str | None = None
    medio: str | None = None
    genero: str | None = None
    extension: str | None = None
    formato_narrativo: str | None = None
    duracion_estimada_min: int | None = None
    sinopsis: str | None = None
    subgenero: str | None = None
    etapa: str | None = None
    pais: str | None = None
    idioma_original: str | None = None

    moneda_principal: str | None = None
    presupuesto_total: int | None = None
    monto_solicitado_iaavim: int | None = None
    monto_aprobado_iaavim: int | None = None
    aporte_privado_monto: int | None = None
    aporte_privado_fuente: str | None = None
    otros_aportes_no_iaavim: list[AporteItem] | None = None
    aportes_en_especie: str | None = None

    monto_estimado_reintegro: int | None = None
    gastos_elegibles: str | None = None
    montos_invertidos_provincia: int | None = None
    distritos_rodaje: list[str] | None = None
    fechas_rodaje: dict | None = None
    postulante_linea_nacional: str | None = None
    postulante_linea_misionera: str | None = None

    carpeta_dossier_path: str | None = None
    presupuesto_detallado_path: str | None = None
    plan_financiamiento_path: str | None = None
    anexos_tecnicos_path: str | None = None
    otros_documentos: list[dict] | None = None

    estado_tramite: str | None = None
    fecha_ingreso: datetime | None = None
    fecha_dictamen: datetime | None = None
    fecha_resolucion: datetime | None = None
    fecha_cierre: datetime | None = None

    pendiente_juridico: bool
    motivo_juridico: str | None = None
    fecha_pendiente_juridico: datetime | None = None
    pendiente_administracion: bool
    motivo_administracion: str | None = None
    fecha_pendiente_administracion: datetime | None = None
    pendiente_agam: bool
    motivo_agam: str | None = None
    fecha_pendiente_agam: datetime | None = None

    comite_asignado_id: int | None = None
    resolucion_otorgamiento_id: int | None = None
    resolucion_otorgamiento_path: str | None = None
    convenio_path: str | None = None

    nro_expediente: str | None = None
    pagos: list[PagoItem] | None = None
    rendicion_estado: str | None = None

    estado_agam: str | None = None
    fecha_entrega_copia: datetime | None = None
    acta_recepcion_path: str | None = None

    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === EVALUADOR ===


class EvaluadorCreate(BaseModel):
    """Schema para crear un Evaluador"""

    # Datos personales
    nombre_completo: str | None = Field(None, max_length=255)
    dni: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=30)
    localidad: str | None = Field(None, max_length=100)
    provincia_pais: str | None = Field(None, max_length=100)
    vinculo_repa: str | None = Field(None, max_length=100)

    # Formación y experiencia
    formacion_academica: str | None = None
    experiencia_audiovisual: str | None = None
    areas_especializacion: list[str] | None = None
    otra_area_especializacion: str | None = Field(None, max_length=255)
    participacion_jurados: str | None = None
    cv_path: str | None = Field(None, max_length=500)
    especialidades: list[str] | None = None

    # Roles y participación
    roles_habilitados: list[str] | None = None
    edicion_linea_evaluada: str | None = Field(None, max_length=255)
    rol: str | None = Field(None, max_length=50)

    # Disponibilidad
    disponible_convocatorias: bool = True
    tipos_convocatoria: list[str] | None = None
    horas_semanales: str | None = Field(None, max_length=20)
    modalidad_preferida: str | None = Field(None, max_length=50)

    # Participación
    emitio_dictamen: bool = False
    resolucion_designacion_path: str | None = Field(None, max_length=500)

    # Contacto y observaciones
    contacto: str | None = Field(None, max_length=255)
    observaciones: str | None = None
    borrador: bool = True


class EvaluadorUpdate(BaseModel):
    """Schema para actualizar un Evaluador"""

    # Datos personales
    nombre_completo: str | None = Field(None, max_length=255)
    dni: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=30)
    localidad: str | None = Field(None, max_length=100)
    provincia_pais: str | None = Field(None, max_length=100)
    vinculo_repa: str | None = Field(None, max_length=100)

    # Formación y experiencia
    formacion_academica: str | None = None
    experiencia_audiovisual: str | None = None
    areas_especializacion: list[str] | None = None
    otra_area_especializacion: str | None = Field(None, max_length=255)
    participacion_jurados: str | None = None
    cv_path: str | None = Field(None, max_length=500)
    especialidades: list[str] | None = None

    # Roles y participación
    roles_habilitados: list[str] | None = None
    edicion_linea_evaluada: str | None = Field(None, max_length=255)
    rol: str | None = Field(None, max_length=50)

    # Disponibilidad
    disponible_convocatorias: bool | None = None
    tipos_convocatoria: list[str] | None = None
    horas_semanales: str | None = Field(None, max_length=20)
    modalidad_preferida: str | None = Field(None, max_length=50)

    # Participación
    emitio_dictamen: bool | None = None
    resolucion_designacion_path: str | None = Field(None, max_length=500)

    # Contacto y observaciones
    contacto: str | None = Field(None, max_length=255)
    observaciones: str | None = None
    borrador: bool | None = None


class EvaluadorOut(BaseModel):
    """Schema de salida para Evaluador"""

    id: int
    user_id: str

    # Datos personales
    nombre_completo: str | None = None
    dni: str | None = None
    email: str | None = None
    telefono: str | None = None
    localidad: str | None = None
    provincia_pais: str | None = None
    vinculo_repa: str | None = None

    # Formación y experiencia
    formacion_academica: str | None = None
    experiencia_audiovisual: str | None = None
    areas_especializacion: list[str] | None = None
    otra_area_especializacion: str | None = None
    participacion_jurados: str | None = None
    cv_path: str | None = None
    especialidades: list[str] | None = None

    # Roles y participación
    roles_habilitados: list[str] | None = None
    edicion_linea_evaluada: str | None = None
    rol: str | None = None

    # Disponibilidad
    disponible_convocatorias: bool = True
    tipos_convocatoria: list[str] | None = None
    horas_semanales: str | None = None
    modalidad_preferida: str | None = None

    # Participación
    emitio_dictamen: bool = False
    resolucion_designacion_path: str | None = None

    # Contacto y observaciones
    contacto: str | None = None
    observaciones: str | None = None
    borrador: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === SEMILLERO DE PRODUCTORES ===

# -- Cohorte --


class CohorteSemilleroCreate(BaseModel):
    """Schema para crear una Cohorte del Semillero"""

    nombre: str = Field(..., max_length=255)
    anio_edicion: int
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    descripcion: str | None = None
    cupo: int | None = None
    estado: str = Field("planificada", max_length=50)
    observaciones: str | None = None


class CohorteSemilleroUpdate(BaseModel):
    """Schema para actualizar una Cohorte"""

    nombre: str | None = Field(None, max_length=255)
    anio_edicion: int | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    descripcion: str | None = None
    cupo: int | None = None
    estado: str | None = Field(None, max_length=50)
    observaciones: str | None = None


class CohorteSemilleroOut(BaseModel):
    """Schema de salida para Cohorte"""

    id: int
    nombre: str
    anio_edicion: int
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    descripcion: str | None = None
    cupo: int | None = None
    estado: str
    observaciones: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -- Participante --


class ParticipanteSemilleroCreate(BaseModel):
    """Schema para crear un Participante del Semillero"""

    cohorte_id: int
    codigo_repa: str | None = Field(None, max_length=50)
    nombre_completo: str | None = Field(None, max_length=255)
    distrito: str | None = Field(None, max_length=100)
    tramites_vinculados: list[int] | None = None
    formacion_previa: str | None = None
    proyectos_en_desarrollo: str | None = None
    participacion_capacitaciones_iaavim: str | None = Field(None, max_length=20)
    diagnostico_inicial: str | None = None
    objetivos: str | None = None
    estado: str = Field("activo", max_length=50)


class ParticipanteSemilleroUpdate(BaseModel):
    """Schema para actualizar un Participante"""

    codigo_repa: str | None = Field(None, max_length=50)
    nombre_completo: str | None = Field(None, max_length=255)
    distrito: str | None = Field(None, max_length=100)
    tramites_vinculados: list[int] | None = None
    formacion_previa: str | None = None
    proyectos_en_desarrollo: str | None = None
    participacion_capacitaciones_iaavim: str | None = Field(None, max_length=20)
    diagnostico_inicial: str | None = None
    objetivos: str | None = None
    estado: str | None = Field(None, max_length=50)
    resultados_cualitativos: str | None = None
    resultados_cuantificables: dict | None = None


class ParticipanteSemilleroOut(BaseModel):
    """Schema de salida para Participante"""

    id: int
    cohorte_id: int
    codigo_repa: str | None = None
    nombre_completo: str | None = None
    distrito: str | None = None
    tramites_vinculados: list[int] | None = None
    formacion_previa: str | None = None
    proyectos_en_desarrollo: str | None = None
    participacion_capacitaciones_iaavim: str | None = None
    diagnostico_inicial: str | None = None
    objetivos: str | None = None
    estado: str
    resultados_cualitativos: str | None = None
    resultados_cuantificables: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -- Acompañamiento --


class AcompanamientoSemilleroCreate(BaseModel):
    """Schema para crear un Acompañamiento"""

    participante_id: int
    tipo: str = Field(..., max_length=50)
    fecha: datetime | None = None
    responsable: str | None = Field(None, max_length=255)
    observaciones: str | None = None
    adjuntos: list[dict] | None = None


class AcompanamientoSemilleroUpdate(BaseModel):
    """Schema para actualizar un Acompañamiento"""

    tipo: str | None = Field(None, max_length=50)
    fecha: datetime | None = None
    responsable: str | None = Field(None, max_length=255)
    observaciones: str | None = None
    adjuntos: list[dict] | None = None


class AcompanamientoSemilleroOut(BaseModel):
    """Schema de salida para Acompañamiento"""

    id: int
    participante_id: int
    tipo: str
    fecha: datetime | None = None
    responsable: str | None = None
    observaciones: str | None = None
    adjuntos: list[dict] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
