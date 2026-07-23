# schemas/lifecycle_schemas.py
"""Campos de salida del ciclo de vida / Código RePA, compartidos por los *Out."""
from datetime import datetime

from pydantic import BaseModel


class RegistroLifecycleOut(BaseModel):
    """Mixin de salida con el estado y el código RePA de una entidad registrable."""

    codigo_repa: str | None = None
    estado: str | None = None
    fecha_envio: datetime | None = None
    fecha_revision: datetime | None = None
    fecha_resolucion: datetime | None = None
    fecha_vigencia_desde: datetime | None = None
    fecha_vigencia_hasta: datetime | None = None
    motivo_observacion: str | None = None
    motivo_rechazo: str | None = None
