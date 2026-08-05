"""
Modelo de Audit Trail para registrar acciones de usuarios.

Permite rastrear quién hizo qué, cuándo y sobre qué recurso.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.database import Base


class AuditLog(Base):
    """
    Modelo para registrar acciones de auditoría.

    Attributes:
        id: Identificador único del registro.
        user_id: ID del usuario que realizó la acción.
        action: Tipo de acción (CREATE, UPDATE, DELETE, LOGIN, LOGOUT).
        resource_type: Tipo de recurso afectado (User, PersonaFisica, etc.).
        resource_id: ID del recurso afectado.
        details: Detalles adicionales (JSONB).
        ip_address: Dirección IP del cliente.
        user_agent: User-Agent del navegador.
        request_id: ID de la request que generó la acción (ver middlewarelogg).
        created_at: Fecha y hora de la acción.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        # Declarado acá para que coincida con lo que crea la migración
        # f7a8b9c0d1e2 (op.create_index con postgresql_using="gin") — sin
        # esto `alembic check` ve el índice en la DB pero no en el modelo y
        # lo marca como drift a eliminar.
        Index("ix_audit_logs_details_gin", "details", postgresql_using="gin"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String, nullable=True)
    # JSONB y no TEXT: así se puede consultar por contenido (qué campo cambió,
    # sobre qué recurso) en vez de traer todo y filtrar en Python.
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    # Correlaciona esta fila con la línea de log canónico de su request.
    request_id = Column(String(64), nullable=True, index=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relación con User (opcional, puede ser acción anónima)
    user = relationship("User", backref="audit_logs")


# Constantes para tipos de acción
class AuditAction:
    """Constantes para tipos de acción de auditoría."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"
    ROLE_CHANGE = "ROLE_CHANGE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    # El registro de un usuario nuevo se emitía como el string suelto
    # "USER_REGISTER", fuera de esta clase, así que no aparecía en el catálogo
    # que puebla el filtro de la pantalla de auditoría.
    USER_REGISTER = "USER_REGISTER"
