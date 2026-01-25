from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from src.models.user_models import User, Role
from src.models.audit_model import AuditLog
from src.schemas.user_schemas import UserOut, UserUpdate

from src.database import get_db
from src.utils import get_password_hash, validar_password, get_current_user, has_user_role

admin_router = APIRouter()

@admin_router.get("/users", response_model=List[UserOut], description="Obtener todos los usuarios")
async def get_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    """
    Obtener todos los usuarios (Sólo para Administradores).
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    users = db.query(User).all()
    return users

@admin_router.get("/{user_id}", response_model=UserOut, description="Obtener un usuario por ID")
async def get_user(user_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Obtener un usuario por ID (Sólo para Administradores).
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user

@admin_router.put("/{user_id}", response_model=UserOut, description="Modificar los datos de un usuario")
async def update_user(user_id: str, user_in: UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Modificar los datos de un usuario por ID (Sólo para Administradores).
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    
    #print(f"Update_User Admin - Password: {user_in.password}") # Debug
    
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )
    
    # Actualizar los datos del usuario
    if user_in.email:
        user.email = user_in.email # Actualizar el correo electrónico si se proporciona y no hay duplicados
    if user_in.password:
        validar_password(user_in.password)
        user.hashed_password = get_password_hash(user_in.password)
    
    # Guardar los cambios
    db.commit()
    db.refresh(user)
    
    # Devolver el usuario actualizado
    return user

@admin_router.put("/{user_id}/roles", response_model=UserOut, description="Modificar los roles de un usuario")
async def update_user_roles(user_id: str, roles: List[int], db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Modificar los roles de un usuario por ID (Sólo para Administradores).
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )
    
    # Buscar los roles en la base de datos
    roles_db = db.query(Role).filter(Role.id.in_(roles)).all()
    if not roles_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Roles no encontrados",
        )
    
    # Actualizar los roles del usuario
    user.roles = roles_db
    
    # Guardar los cambios
    db.commit()
    db.refresh(user)
    
    # Devolver el usuario actualizado
    return user

# Cambiar estado de is_active True/False
@admin_router.delete("/{user_id}", description="Cambiar estado de 'is_active' del usuario 'user_id', solo para administrador.")
async def delete_user(user_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Cambiar estado de is_active True/False.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@admin_router.get("/audit-logs", description="Obtener registros de auditoría")
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    action: Optional[str] = Query(None, description="Filtrar por acción (USER_LOGIN, USER_REGISTER, etc.)"),
    user_id: Optional[str] = Query(None, description="Filtrar por ID de usuario"),
    days: int = Query(7, description="Días hacia atrás a consultar (default: 7)"),
    limit: int = Query(100, description="Límite de registros (default: 100, max: 500)")
):
    """
    Obtener registros de auditoría (Sólo para Administradores).
    
    Permite filtrar por:
    - action: tipo de acción (USER_LOGIN, USER_REGISTER, PASSWORD_CHANGE, etc.)
    - user_id: ID del usuario específico
    - days: cantidad de días hacia atrás
    - limit: cantidad máxima de registros
    """
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )
    
    # Limitar el máximo de registros
    limit = min(limit, 500)
    
    # Calcular fecha de inicio
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Construir query
    query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Ordenar por fecha descendente y limitar
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "user_id": log.user_id,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]
