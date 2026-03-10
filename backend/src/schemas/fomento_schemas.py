# schemas/fomento_schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    monto_aprobado_iaavim: int | None = None
    aporte_privado_monto: int | None = None
    aporte_privado_fuente: str | None = Field(None, max_length=255)
    otros_aportes_no_iaavim: list[dict] | None = None
    aportes_en_especie: str | None = None

    carpeta_dossier_path: str | None = Field(None, max_length=500)
    presupuesto_detallado_path: str | None = Field(None, max_length=500)
    plan_financiamiento_path: str | None = Field(None, max_length=500)
    anexos_tecnicos_path: str | None = Field(None, max_length=500)

    estado_tramite: str | None = Field(None, max_length=50)
    fecha_ingreso: datetime | None = None
    fecha_dictamen: datetime | None = None
    fecha_resolucion: datetime | None = None
    fecha_cierre: datetime | None = None

    pendiente_juridico: bool = False
    motivo_juridico: str | None = Field(None, max_length=255)
    fecha_pendiente_juridico: datetime | None = None
    pendiente_administracion: bool = False
    motivo_administracion: str | None = Field(None, max_length=255)
    fecha_pendiente_administracion: datetime | None = None
    pendiente_agam: bool = False
    motivo_agam: str | None = Field(None, max_length=255)
    fecha_pendiente_agam: datetime | None = None

    comite_asignado_id: int | None = None
    resolucion_otorgamiento_id: int | None = None
    resolucion_otorgamiento_path: str | None = Field(None, max_length=500)
    convenio_path: str | None = Field(None, max_length=500)

    nro_expediente: str | None = Field(None, max_length=50)
    pagos: list[dict] | None = None
    rendicion_estado: str | None = Field(None, max_length=50)

    estado_agam: str | None = Field(None, max_length=50)
    fecha_entrega_copia: datetime | None = None
    acta_recepcion_path: str | None = Field(None, max_length=500)

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
    monto_aprobado_iaavim: int | None = None
    aporte_privado_monto: int | None = None
    aporte_privado_fuente: str | None = Field(None, max_length=255)
    otros_aportes_no_iaavim: list[dict] | None = None
    aportes_en_especie: str | None = None

    carpeta_dossier_path: str | None = Field(None, max_length=500)
    presupuesto_detallado_path: str | None = Field(None, max_length=500)
    plan_financiamiento_path: str | None = Field(None, max_length=500)
    anexos_tecnicos_path: str | None = Field(None, max_length=500)

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
    pagos: list[dict] | None = None
    rendicion_estado: str | None = Field(None, max_length=50)

    estado_agam: str | None = Field(None, max_length=50)
    fecha_entrega_copia: datetime | None = None
    acta_recepcion_path: str | None = Field(None, max_length=500)

    borrador: bool | None = None


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
    otros_aportes_no_iaavim: list[dict] | None = None
    aportes_en_especie: str | None = None

    carpeta_dossier_path: str | None = None
    presupuesto_detallado_path: str | None = None
    plan_financiamiento_path: str | None = None
    anexos_tecnicos_path: str | None = None

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
    pagos: list[dict] | None = None
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
