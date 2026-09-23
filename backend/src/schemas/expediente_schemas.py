# schemas/expediente_schemas.py
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExpedienteCreate(BaseModel):
    """Schema para crear un Expediente Administrativo.

    Todos los campos son opcionales: el area carga el expediente apenas se
    inicia y va completando montos, resolucion y pago a medida que avanza el
    tramite (el PM dejo fuera de esta version las validaciones de
    obligatoriedad de ID / fecha / area).
    """
    borrador: bool = False

    numero_expediente_provincial: str | None = Field(None, max_length=100)
    fecha_alta: date | None = None

    tipo_expediente: str | None = Field(None, max_length=50)
    otro_tipo: str | None = Field(None, max_length=255)
    area_solicitante: str | None = Field(None, max_length=50)

    nombre_proyecto: str | None = Field(None, max_length=255)
    codigo_repa: str | None = Field(None, max_length=50)

    resolucion_id: str | None = Field(None, max_length=100)
    # Path devuelto por /upload/document/{doc_type}; el archivo no viaja aca.
    resolucion_pdf_path: str | None = Field(None, max_length=500)

    estado_expediente: str | None = Field(None, max_length=50)

    monto_solicitado: Decimal | None = None
    monto_aprobado: Decimal | None = None
    monto_ejecutado: Decimal | None = None

    fuente_presupuestaria: str | None = Field(None, max_length=50)
    fecha_pago_final: date | None = None
    forma_pago: str | None = Field(None, max_length=30)

    genera_informe_financiero: str | None = Field(None, max_length=20)
    genera_devolucion: bool | None = None
    observaciones_administrativas: str | None = None


class ExpedienteUpdate(BaseModel):
    """Schema para actualizar un Expediente Administrativo (PUT parcial).

    Mismo cuerpo que Create; se aplica con exclude_unset para poder tocar un
    solo campo (tipico: pasar el estado a 'pagado' y cargar monto_ejecutado).
    """
    borrador: bool | None = None

    numero_expediente_provincial: str | None = Field(None, max_length=100)
    fecha_alta: date | None = None

    tipo_expediente: str | None = Field(None, max_length=50)
    otro_tipo: str | None = Field(None, max_length=255)
    area_solicitante: str | None = Field(None, max_length=50)

    nombre_proyecto: str | None = Field(None, max_length=255)
    codigo_repa: str | None = Field(None, max_length=50)

    resolucion_id: str | None = Field(None, max_length=100)
    resolucion_pdf_path: str | None = Field(None, max_length=500)

    estado_expediente: str | None = Field(None, max_length=50)

    monto_solicitado: Decimal | None = None
    monto_aprobado: Decimal | None = None
    monto_ejecutado: Decimal | None = None

    fuente_presupuestaria: str | None = Field(None, max_length=50)
    fecha_pago_final: date | None = None
    forma_pago: str | None = Field(None, max_length=30)

    genera_informe_financiero: str | None = Field(None, max_length=20)
    genera_devolucion: bool | None = None
    observaciones_administrativas: str | None = None


class ExpedienteOut(BaseModel):
    """Schema de salida de un Expediente Administrativo."""
    borrador: bool = False

    id: int

    numero_expediente_provincial: str | None = None
    fecha_alta: date | None = None

    tipo_expediente: str | None = None
    otro_tipo: str | None = None
    area_solicitante: str | None = None

    nombre_proyecto: str | None = None
    codigo_repa: str | None = None

    resolucion_id: str | None = None
    resolucion_pdf_path: str | None = None

    estado_expediente: str | None = None

    monto_solicitado: Decimal | None = None
    monto_aprobado: Decimal | None = None
    monto_ejecutado: Decimal | None = None

    fuente_presupuestaria: str | None = None
    fecha_pago_final: date | None = None
    forma_pago: str | None = None

    genera_informe_financiero: str | None = None
    genera_devolucion: bool | None = None
    observaciones_administrativas: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExpedienteListOut(BaseModel):
    """Pagina del listado de backoffice."""

    items: list[ExpedienteOut]
    total: int
    offset: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class ResumenEjecucionOut(BaseModel):
    """Ejecucion presupuestaria de un area en un anio."""

    area_solicitante: str | None = None
    anio: int | None = None
    monto_aprobado: Decimal
    monto_ejecutado: Decimal
    # None cuando no hay monto aprobado: dividir por cero no es 0% de ejecucion,
    # es "no hay presupuesto contra el cual medir".
    porcentaje_ejecucion: float | None = None

    model_config = ConfigDict(from_attributes=True)


class ResumenTipoOut(BaseModel):
    """Cantidad y montos agrupados por tipo de expediente."""

    tipo_expediente: str | None = None
    cantidad: int
    monto_solicitado: Decimal
    monto_aprobado: Decimal
    monto_ejecutado: Decimal

    model_config = ConfigDict(from_attributes=True)


class ExpedienteResumenOut(BaseModel):
    """Indicadores del modulo (ver GET /stats/resumen)."""

    ejecucion_por_area_anio: list[ResumenEjecucionOut]
    por_tipo_expediente: list[ResumenTipoOut]

    model_config = ConfigDict(from_attributes=True)
