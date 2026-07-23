# schemas/rodaje_schemas.py
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# === Locación (objeto anidado) ===
class LocacionRodaje(BaseModel):
    """Schema para una locación de rodaje"""

    municipio: str | None = None
    direccion: str | None = None
    espacio: str | None = None  # publico, privado
    num_personas: int | None = None
    servicios_requeridos: str | None = None


# === RODAJE CREATE ===
class RodajeCreate(BaseModel):
    """Schema para crear un Rodaje (Alta o Finalización)"""

    # 1. Tipo de registro
    tipo_registro: str | None = Field(None, max_length=30)

    # 2. Datos generales del proyecto
    titulo_produccion: str | None = Field(None, max_length=255)
    tipo_produccion: str | None = Field(None, max_length=50)
    otro_tipo_produccion: str | None = Field(None, max_length=100)
    genero: str | None = Field(None, max_length=100)
    clasificacion: str | None = Field(None, max_length=50)
    otra_clasificacion: str | None = Field(None, max_length=100)
    pais_produccion: str | None = Field(None, max_length=100)
    idioma_original: str | None = Field(None, max_length=50)
    sinopsis: str | None = Field(None, max_length=500)
    anio_rodaje: int | None = None
    codigo_repa_productora: str | None = Field(None, max_length=50)
    codigos_repa_responsables: list[str] | None = None
    id_proyecto_fomento: str | None = Field(None, max_length=50)

    # 3. Productora responsable
    nombre_productora: str | None = Field(None, max_length=255)
    cuit_productora: str | None = Field(None, max_length=13)
    representante_legal: str | None = Field(None, max_length=200)
    productor_campo: str | None = Field(None, max_length=200)
    email_productora: EmailStr | None = None
    telefono_productora: str | None = Field(None, max_length=50)
    provincia_pais_origen: str | None = Field(None, max_length=100)

    # 4. Información del rodaje
    fecha_inicio_rodaje: date | None = None
    fecha_fin_rodaje: date | None = None
    locaciones: list[LocacionRodaje] | None = None
    cantidad_permisos: int | None = None
    vehiculos_equipamiento: str | None = None

    # 5. Carta de aval
    requiere_carta_aval: bool = False
    destino_aval: str | None = Field(None, max_length=50)
    otro_destino_aval: str | None = Field(None, max_length=100)
    motivo_aval: str | None = None
    fecha_limite_aval: date | None = None

    # 6. Documentación obligatoria
    tiene_poliza_seguro: bool = False
    tiene_acuerdo_indemnizacion: bool = False
    tiene_autorizaciones_privados: bool = False
    tiene_fotos_locaciones: bool = False
    tiene_permisos_especiales: bool = False
    documentos_adjuntos: list[dict] | None = None

    # 7. Impacto y cierre (Finalización)
    fecha_real_finalizacion: date | None = None
    cantidad_tecnicos_locales: int | None = None
    cantidad_artistas_locales: int | None = None
    descripcion_beneficios_locales: str | None = None
    medidas_ambientales: str | None = None
    compromisos_comunitarios: str | None = None
    informe_rodaje: str | None = Field(None, max_length=500)

    # NOTA: los campos de seguimiento (estado_tramite, inspector, pagos,
    # observaciones internas, etc.) NO están acá a propósito — solo pueden
    # modificarse vía RodajeAdminUpdate en las rutas admin. Un solicitante
    # no debe poder autoaprobar su permiso de filmación.

    # Metadatos
    borrador: bool = False


# === RODAJE UPDATE ===
class RodajeUpdate(BaseModel):
    """Schema para actualizar un Rodaje"""

    # 1. Tipo de registro
    tipo_registro: str | None = Field(None, max_length=30)

    # 2. Datos generales del proyecto
    titulo_produccion: str | None = Field(None, max_length=255)
    tipo_produccion: str | None = Field(None, max_length=50)
    otro_tipo_produccion: str | None = Field(None, max_length=100)
    genero: str | None = Field(None, max_length=100)
    clasificacion: str | None = Field(None, max_length=50)
    otra_clasificacion: str | None = Field(None, max_length=100)
    pais_produccion: str | None = Field(None, max_length=100)
    idioma_original: str | None = Field(None, max_length=50)
    sinopsis: str | None = Field(None, max_length=500)
    anio_rodaje: int | None = None
    codigo_repa_productora: str | None = Field(None, max_length=50)
    codigos_repa_responsables: list[str] | None = None
    id_proyecto_fomento: str | None = Field(None, max_length=50)

    # 3. Productora responsable
    nombre_productora: str | None = Field(None, max_length=255)
    cuit_productora: str | None = Field(None, max_length=13)
    representante_legal: str | None = Field(None, max_length=200)
    productor_campo: str | None = Field(None, max_length=200)
    email_productora: EmailStr | None = None
    telefono_productora: str | None = Field(None, max_length=50)
    provincia_pais_origen: str | None = Field(None, max_length=100)

    # 4. Información del rodaje
    fecha_inicio_rodaje: date | None = None
    fecha_fin_rodaje: date | None = None
    locaciones: list[LocacionRodaje] | None = None
    cantidad_permisos: int | None = None
    vehiculos_equipamiento: str | None = None

    # 5. Carta de aval
    requiere_carta_aval: bool | None = None
    destino_aval: str | None = Field(None, max_length=50)
    otro_destino_aval: str | None = Field(None, max_length=100)
    motivo_aval: str | None = None
    fecha_limite_aval: date | None = None

    # 6. Documentación obligatoria
    tiene_poliza_seguro: bool | None = None
    tiene_acuerdo_indemnizacion: bool | None = None
    tiene_autorizaciones_privados: bool | None = None
    tiene_fotos_locaciones: bool | None = None
    tiene_permisos_especiales: bool | None = None
    documentos_adjuntos: list[dict] | None = None

    # 7. Impacto y cierre (Finalización)
    fecha_real_finalizacion: date | None = None
    cantidad_tecnicos_locales: int | None = None
    cantidad_artistas_locales: int | None = None
    descripcion_beneficios_locales: str | None = None
    medidas_ambientales: str | None = None
    compromisos_comunitarios: str | None = None
    informe_rodaje: str | None = Field(None, max_length=500)

    # NOTA: sin campos de seguimiento — ver nota en RodajeCreate.

    # Metadatos
    borrador: bool | None = None


class RodajeAdminUpdate(RodajeUpdate):
    """Schema para actualización admin de un Rodaje.

    Extiende el schema de usuario con los campos de seguimiento
    administrativo. Solo se usa en las rutas /admin/* (rodajes:manage).
    """

    # 8. Seguimiento (solo admin)
    estado_tramite: str | None = Field(None, max_length=30)
    fecha_evaluacion: date | None = None
    fecha_emision_permiso: date | None = None
    tarifas_aplicadas: str | None = None
    pagos_realizados: str | None = None
    inspector_asignado: str | None = Field(None, max_length=200)
    informe_inspeccion: str | None = None
    observaciones_internas: str | None = None


# === RODAJE OUT ===
class RodajeOut(BaseModel):
    """Schema de salida para Rodaje"""

    id: int
    user_id: str

    # 1. Tipo de registro
    tipo_registro: str | None = None

    # 2. Datos generales del proyecto
    titulo_produccion: str | None = None
    tipo_produccion: str | None = None
    otro_tipo_produccion: str | None = None
    genero: str | None = None
    clasificacion: str | None = None
    otra_clasificacion: str | None = None
    pais_produccion: str | None = None
    idioma_original: str | None = None
    sinopsis: str | None = None
    anio_rodaje: int | None = None
    codigo_repa_productora: str | None = None
    codigos_repa_responsables: list[str] | None = None
    id_proyecto_fomento: str | None = None

    # 3. Productora responsable
    nombre_productora: str | None = None
    cuit_productora: str | None = None
    representante_legal: str | None = None
    productor_campo: str | None = None
    email_productora: str | None = None
    telefono_productora: str | None = None
    provincia_pais_origen: str | None = None

    # 4. Información del rodaje
    fecha_inicio_rodaje: date | None = None
    fecha_fin_rodaje: date | None = None
    locaciones: Any | None = None  # JSON
    cantidad_permisos: int | None = None
    vehiculos_equipamiento: str | None = None

    # 5. Carta de aval
    requiere_carta_aval: bool = False
    destino_aval: str | None = None
    otro_destino_aval: str | None = None
    motivo_aval: str | None = None
    fecha_limite_aval: date | None = None

    # 6. Documentación obligatoria
    tiene_poliza_seguro: bool = False
    tiene_acuerdo_indemnizacion: bool = False
    tiene_autorizaciones_privados: bool = False
    tiene_fotos_locaciones: bool = False
    tiene_permisos_especiales: bool = False
    documentos_adjuntos: Any | None = None  # JSON

    # 7. Impacto y cierre
    fecha_real_finalizacion: date | None = None
    cantidad_tecnicos_locales: int | None = None
    cantidad_artistas_locales: int | None = None
    descripcion_beneficios_locales: str | None = None
    medidas_ambientales: str | None = None
    compromisos_comunitarios: str | None = None
    informe_rodaje: str | None = None

    # 8. Seguimiento
    estado_tramite: str = "recibido"
    fecha_evaluacion: date | None = None
    fecha_emision_permiso: date | None = None
    tarifas_aplicadas: str | None = None
    pagos_realizados: str | None = None
    inspector_asignado: str | None = None
    informe_inspeccion: str | None = None
    observaciones_internas: str | None = None

    # Metadatos
    borrador: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === LISTA DE RODAJES ===
class RodajeListOut(BaseModel):
    """Schema resumido para listar rodajes"""

    id: int
    titulo_produccion: str | None = None
    tipo_produccion: str | None = None
    nombre_productora: str | None = None
    anio_rodaje: int | None = None
    estado_tramite: str = "recibido"
    tipo_registro: str | None = None
    fecha_inicio_rodaje: date | None = None
    borrador: bool = False
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
