# models/registro_lifecycle.py
"""Ciclo de vida común de las entidades registrables del RePA.

Define:
- ``EstadoRegistro``: máquina de estados del registro (borrador → ... → aprobado → vigente/vencido).
- ``RegistroLifecycleMixin``: columnas compartidas (código RePA, estado, timestamps de
  transición, vigencia, motivos y revisor) que se aplican a PF, PJ, AS, AGAM y ESA.
- ``RepaCodeCounter``: contador secuencial por tipo de entidad para emitir el código RePA
  de forma atómica.

El formato exacto del código (ancho de secuencia, prefijos) está encapsulado en
``src.services.repa_code_service`` para poder ajustarlo sin tocar los modelos.
"""

import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declared_attr

from src.database import Base


class EstadoRegistro(str, enum.Enum):
    """Estados del ciclo de vida de un registro del Padrón RePA."""

    borrador = "borrador"
    enviado = "enviado"
    en_revision = "en_revision"
    observado = "observado"
    rechazado = "rechazado"
    aprobado = "aprobado"
    vigente = "vigente"
    vencido = "vencido"


class RegistroLifecycleMixin:
    """Columnas comunes de ciclo de vida y código RePA para entidades registrables.

    Se almacena ``estado`` como ``String`` (no enum SQL) para evitar la complejidad de los
    tipos enum de PostgreSQL en migraciones; la validación se hace en la capa de servicio
    usando :class:`EstadoRegistro`.
    """

    # Código RePA emitido al aprobar (inmutable una vez asignado). Nullable hasta entonces.
    codigo_repa = Column(String(30), unique=True, nullable=True, index=True)

    # Estado del ciclo de vida. Indexado: el backoffice (padrón admin) filtra
    # y pagina por estado constantemente.
    estado = Column(
        String(20),
        nullable=False,
        default=EstadoRegistro.borrador.value,
        server_default=EstadoRegistro.borrador.value,
        index=True,
    )

    # Última vez que el titular modificó datos del registro. Distinta de
    # fecha_envio (que marca el envío a revisión) y de fecha_resolucion (que
    # marca la decisión del revisor): esta responde "¿cuán actualizado está el
    # dato que figura en el padrón?".
    fecha_ultima_actualizacion = Column(DateTime(timezone=True), nullable=True)

    # Timestamps de transición.
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    fecha_revision = Column(DateTime(timezone=True), nullable=True)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)

    # Vigencia (el código no caduca; los formularios sí, anualmente).
    fecha_vigencia_desde = Column(DateTime(timezone=True), nullable=True)
    fecha_vigencia_hasta = Column(DateTime(timezone=True), nullable=True)

    # Motivos de observación/rechazo del revisor.
    motivo_observacion = Column(Text, nullable=True)
    motivo_rechazo = Column(Text, nullable=True)

    @declared_attr
    def revisado_por(cls):
        # FK al usuario admin que resolvió la revisión.
        return Column(String, ForeignKey("users.id"), nullable=True)


class RepaCodeCounter(Base):
    """Contador secuencial por tipo de entidad para emitir códigos RePA.

    Una fila por tipo (``PF``, ``PJ``, ``AS``, ``ESA``, ``AGAM``). La emisión se hace con
    bloqueo de fila (``SELECT ... FOR UPDATE``) en el servicio para evitar duplicados.
    """

    __tablename__ = "repa_code_counters"

    tipo = Column(String(10), primary_key=True)
    last_value = Column(Integer, nullable=False, default=0, server_default="0")
