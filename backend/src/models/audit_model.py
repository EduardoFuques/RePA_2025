"""
Modelo de Audit Trail para registrar acciones de usuarios.

Permite rastrear quién hizo qué, cuándo y sobre qué recurso.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
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
        details: Detalles adicionales en formato JSON.
        ip_address: Dirección IP del cliente.
        user_agent: User-Agent del navegador.
        created_at: Fecha y hora de la acción.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
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
