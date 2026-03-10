"""
Servicio de Audit Trail para registrar acciones de usuarios.

Uso:
    from src.audit import audit_log

    audit_log(
        db=db,
        user_id=current_user["id"],
        action=AuditAction.CREATE,
        resource_type="PersonaFisica",
        resource_id=str(persona.id),
        details={"campos": ["nombre", "apellido"]},
        request=request
    )
"""

import json

from fastapi import Request
from sqlalchemy.orm import Session

from src.logger import logger
from src.models.audit_model import AuditLog


def audit_log(
    db: Session,
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    """
    Registra una acción en el audit trail.

    Args:
        db: Sesión de base de datos.
        action: Tipo de acción (usar constantes de AuditAction).
        user_id: ID del usuario que realiza la acción.
        resource_type: Tipo de recurso afectado.
        resource_id: ID del recurso afectado.
        details: Diccionario con detalles adicionales.
        request: Objeto Request para extraer IP y User-Agent.

    Returns:
        AuditLog: Registro de auditoría creado.
    """
    ip_address = None
    user_agent = None

    if request:
        # Obtener IP del cliente usando la misma lógica que el rate limiter
        # (solo confía en X-Forwarded-For si viene de un proxy confiable)
        from src.rate_limiter import get_client_ip

        ip_address = get_client_ip(request)

        user_agent = request.headers.get("User-Agent", "")[:500]

    # Serializar details a JSON
    details_json = json.dumps(details, ensure_ascii=False) if details else None

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_json,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

        logger.info(
            f"Audit: {action} - User: {user_id} - Resource: {resource_type}/{resource_id}"
        )

        return audit_entry
    except Exception as e:
        logger.error(f"Error registrando audit log: {e}")
        db.rollback()
        raise


def get_audit_logs(
    db: Session,
    user_id: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """
    Obtiene registros de auditoría con filtros opcionales.

    Args:
        db: Sesión de base de datos.
        user_id: Filtrar por usuario.
        action: Filtrar por tipo de acción.
        resource_type: Filtrar por tipo de recurso.
        limit: Cantidad máxima de registros.
        offset: Desplazamiento para paginación.

    Returns:
        list[AuditLog]: Lista de registros de auditoría.
    """
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
