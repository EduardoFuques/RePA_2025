# schemas/instrumento_juridico_schemas.py
"""
Schemas Pydantic v2 del módulo de Instrumentos Jurídicos.

Los desplegables no se validan con field_validator: la fuente de verdad son los
CheckConstraint del modelo (convención del repo), así no hay dos listas de
opciones que se puedan desincronizar.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# === ACTA DEL CONSEJO DIRECTIVO (bloque condicional, sección 4) ===
class AsistenteActa(BaseModel):
    """Asistente registrado en una reunión del Consejo Directivo"""

    nombre: str | None = Field(None, max_length=200)
    cargo: str | None = Field(None, max_length=200)
    organizacion: str | None = Field(None, max_length=200)


class ActaConsejoCreate(BaseModel):
    """Datos del acta. Solo aplica si tipo_documento == 'acta_consejo_directivo'."""

    fecha_reunion: date | None = None
    asistentes: list[AsistenteActa] | None = None
    ordenes_del_dia: str | None = None
    decisiones_tomadas: str | None = None
    acta_pdf_path: str | None = Field(None, max_length=500)
    resoluciones_emitidas: list[str] | None = None


class ActaConsejoOut(BaseModel):
    """Schema de salida del acta del Consejo Directivo"""

    id: int
    instrumento_id: int
    fecha_reunion: date | None = None
    asistentes: Any | None = None  # JSON
    ordenes_del_dia: str | None = None
    decisiones_tomadas: str | None = None
    acta_pdf_path: str | None = None
    resoluciones_emitidas: Any | None = None  # JSON
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# === INSTRUMENTO CREATE ===
class InstrumentoCreate(BaseModel):
    """Schema para dar de alta un instrumento jurídico"""
    borrador: bool = False

    # 1. Datos generales
    # Los campos que el formulario marca obligatorios son opcionales en el
    # ESQUEMA y se validan al ENVIAR (borrador=False), en la ruta. Si no,
    # el autoguardado no podria crear la fila con el primer campo escrito.
    tipo_documento: str | None = Field(None, max_length=50)
    otro_tipo_documento: str | None = Field(None, max_length=100)
    numero_instrumento: str | None = Field(None, max_length=100)
    version: str | None = Field(None, max_length=50)
    fecha_emision: date | None = None
    titulo: str | None = Field(None, max_length=500)
    resumen: str | None = None
    palabras_clave: list[str] | None = Field(None, max_length=5)
    ambito_aplicacion: str | None = Field(None, max_length=30)
    archivo_pdf_path: str | None = Field(None, max_length=500)
    # Path devuelto por upload_routes; acá solo se guarda la referencia.

    # 2. Vigencia y cumplimiento
    fecha_inicio_vigencia: date | None = None
    fecha_expiracion: date | None = None
    condiciones_finalizacion: list[str] | None = None
    otra_condicion_finalizacion: str | None = Field(None, max_length=255)

    # 3. Tematización
    areas_vinculadas: list[str] | None = None
    tematica_principal: str | None = Field(None, max_length=50)
    otra_tematica: str | None = Field(None, max_length=100)
    vinculado_resolucion_previa: bool = False
    resolucion_previa_id: str | None = Field(None, max_length=100)

    # 5. Vinculación institucional y publicidad
    codigo_repa_vinculado: str | None = Field(None, max_length=50)
    vinculado_proyecto: str | None = Field(None, max_length=20)
    proyecto_id: str | None = Field(None, max_length=100)
    area_responsable_seguimiento: str | None = Field(None, max_length=200)
    requiere_publicacion: str | None = Field(None, max_length=20)
    notas_internas: str | None = None

    # 6. Observaciones
    observaciones_adicionales: str | None = None

    # 7. Estado de revisión jurídica (el resto de los campos del sistema —
    # usuario_carga_id, created_at, updated_at — los completa el backend).
    estado_revision: str | None = Field(None, max_length=20)

    # 4. Bloque condicional del acta
    acta: ActaConsejoCreate | None = None


# === INSTRUMENTO UPDATE ===
class InstrumentoUpdate(BaseModel):
    """Schema para actualizar un instrumento jurídico (todos los campos opcionales)"""
    borrador: bool | None = None

    tipo_documento: str | None = Field(None, max_length=50)
    otro_tipo_documento: str | None = Field(None, max_length=100)
    numero_instrumento: str | None = Field(None, max_length=100)
    version: str | None = Field(None, max_length=50)
    fecha_emision: date | None = None
    titulo: str | None = Field(None, max_length=500)
    resumen: str | None = None
    palabras_clave: list[str] | None = Field(None, max_length=5)
    ambito_aplicacion: str | None = Field(None, max_length=30)
    archivo_pdf_path: str | None = Field(None, max_length=500)

    fecha_inicio_vigencia: date | None = None
    fecha_expiracion: date | None = None
    condiciones_finalizacion: list[str] | None = None
    otra_condicion_finalizacion: str | None = Field(None, max_length=255)

    areas_vinculadas: list[str] | None = None
    tematica_principal: str | None = Field(None, max_length=50)
    otra_tematica: str | None = Field(None, max_length=100)
    vinculado_resolucion_previa: bool | None = None
    resolucion_previa_id: str | None = Field(None, max_length=100)

    codigo_repa_vinculado: str | None = Field(None, max_length=50)
    vinculado_proyecto: str | None = Field(None, max_length=20)
    proyecto_id: str | None = Field(None, max_length=100)
    area_responsable_seguimiento: str | None = Field(None, max_length=200)
    requiere_publicacion: str | None = Field(None, max_length=20)
    notas_internas: str | None = None

    observaciones_adicionales: str | None = None
    estado_revision: str | None = Field(None, max_length=20)

    # Si viene, se crea o se pisa el acta asociada (upsert del bloque 1:1).
    acta: ActaConsejoCreate | None = None


# === INSTRUMENTO OUT ===
class InstrumentoOut(BaseModel):
    """Schema de salida completo de un instrumento jurídico"""
    borrador: bool = False

    id: int

    tipo_documento: str | None = None
    otro_tipo_documento: str | None = None
    numero_instrumento: str | None = None
    version: str | None = None
    fecha_emision: date | None = None
    titulo: str | None = None
    resumen: str | None = None
    palabras_clave: Any | None = None  # JSON
    ambito_aplicacion: str | None = None
    archivo_pdf_path: str | None = None

    fecha_inicio_vigencia: date | None = None
    fecha_expiracion: date | None = None
    condiciones_finalizacion: Any | None = None  # JSON
    otra_condicion_finalizacion: str | None = None

    areas_vinculadas: Any | None = None  # JSON
    tematica_principal: str | None = None
    otra_tematica: str | None = None
    vinculado_resolucion_previa: bool = False
    resolucion_previa_id: str | None = None

    codigo_repa_vinculado: str | None = None
    vinculado_proyecto: str | None = None
    proyecto_id: str | None = None
    area_responsable_seguimiento: str | None = None
    requiere_publicacion: str | None = None
    notas_internas: str | None = None

    observaciones_adicionales: str | None = None

    usuario_carga_id: str
    estado_revision: str = "en_revision"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    acta: ActaConsejoOut | None = None

    model_config = ConfigDict(from_attributes=True)


# === LISTADO ===
class InstrumentoListOut(BaseModel):
    """Schema resumido para el listado paginado del digesto"""
    borrador: bool = False

    id: int
    tipo_documento: str | None = None
    numero_instrumento: str | None = None
    titulo: str | None = None
    fecha_emision: date | None = None
    ambito_aplicacion: str | None = None
    tematica_principal: str | None = None
    areas_vinculadas: Any | None = None  # JSON
    fecha_inicio_vigencia: date | None = None
    fecha_expiracion: date | None = None
    estado_revision: str = "en_revision"
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
