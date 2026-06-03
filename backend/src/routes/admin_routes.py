"""
Rutas de administración del sistema RePA.

Endpoints protegidos por permisos granulares (RBAC). Incluye:
- Gestión de usuarios (listar, modificar, activar/desactivar, asignar roles)
- Gestión de roles y permisos
- Consulta de logs de auditoría

IMPORTANTE: las rutas estáticas (`/users`, `/roles`, `/permissions`,
`/audit-logs`) se declaran como prefijos propios y los recursos por ID quedan
anidados (`/users/{id}`, `/roles/{id}`) para evitar colisiones de routing.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.audit_model import AuditLog
from src.models.user_models import Permission, Role, User
from src.rbac import SYSTEM_ROLE_NAMES
from src.schemas.user_schemas import (
    PermissionOut,
    RoleCreate,
    RoleDetailOut,
    RoleUpdate,
    UserOut,
    UserRolePatch,
    UserUpdate,
)
from src.utils import (
    get_password_hash,
    require_permissions,
    validar_password,
    verify_email_unique,
)

admin_router = APIRouter()


def _resolve_permissions(db: Session, codes: list[str]) -> list[Permission]:
    """Resuelve códigos de permiso a entidades Permission; valida que existan."""
    if not codes:
        return []
    unique_codes = list(set(codes))
    perms = db.query(Permission).filter(Permission.code.in_(unique_codes)).all()
    found = {p.code for p in perms}
    invalid = set(unique_codes) - found
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permisos inválidos: {', '.join(sorted(invalid))}",
        )
    return perms


# ============================================================
# PERMISOS
# ============================================================
@admin_router.get(
    "/permissions",
    response_model=list[PermissionOut],
    summary="Listar catálogo de permisos",
)
async def list_permissions(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("roles:read")),
):
    """Listar todos los permisos disponibles en el sistema."""
    return db.query(Permission).order_by(Permission.code).all()


# ============================================================
# ROLES
# ============================================================
@admin_router.get(
    "/roles", response_model=list[RoleDetailOut], summary="Listar roles"
)
async def list_roles(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("roles:read")),
):
    """Listar todos los roles con sus permisos."""
    return db.query(Role).order_by(Role.id).all()


@admin_router.post(
    "/roles",
    response_model=RoleDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un rol",
)
async def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("roles:manage")),
):
    """Crear un nuevo rol con permisos granulares."""
    nombre = data.rol.strip()
    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del rol es obligatorio",
        )
    existing = (
        db.query(Role).filter(func.lower(Role.rol) == nombre.lower()).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un rol con ese nombre",
        )
    role = Role(rol=nombre, descripcion=data.descripcion, is_system=False)
    role.permissions = _resolve_permissions(db, data.permissions)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@admin_router.put(
    "/roles/{role_id}", response_model=RoleDetailOut, summary="Actualizar un rol"
)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("roles:manage")),
):
    """Actualizar un rol. Los roles del sistema no pueden renombrarse."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )

    if data.rol is not None and data.rol.strip().lower() != role.rol.lower():
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede renombrar un rol del sistema",
            )
        nuevo = data.rol.strip()
        if (
            db.query(Role)
            .filter(func.lower(Role.rol) == nuevo.lower(), Role.id != role_id)
            .first()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre",
            )
        role.rol = nuevo

    if data.descripcion is not None:
        role.descripcion = data.descripcion

    if data.permissions is not None:
        role.permissions = _resolve_permissions(db, data.permissions)

    db.commit()
    db.refresh(role)
    return role


@admin_router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un rol",
)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("roles:manage")),
):
    """Eliminar un rol. Los roles del sistema no pueden eliminarse."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado"
        )
    if role.is_system or role.rol.lower() in SYSTEM_ROLE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un rol del sistema",
        )
    db.delete(role)
    db.commit()
    return None


@admin_router.get(
    "/users",
    response_model=list[UserOut],
    summary="Listar todos los usuarios",
    responses={
        200: {"description": "Lista de usuarios"},
        403: {"description": "No autorizado (requiere rol admin)"},
    },
)
async def get_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("users:read")),
):
    """Obtener todos los usuarios registrados en el sistema."""
    return db.query(User).all()


def _get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return user


@admin_router.get(
    "/users/{user_id}", response_model=UserOut, summary="Obtener un usuario por ID"
)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("users:read")),
):
    """Obtener un usuario por ID."""
    return _get_user_or_404(db, user_id)


@admin_router.put(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Modificar los datos de un usuario",
)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("users:write")),
):
    """Modificar email y/o contraseña de un usuario."""
    user = _get_user_or_404(db, user_id)

    if user_in.email and user_in.email != user.email:
        # Validar unicidad de email para evitar IntegrityError 500
        verify_email_unique(
            db, user_in, {"id": user.id, "email": user.email}
        )
        user.email = user_in.email
    if user_in.password:
        validar_password(user_in.password)
        user.hashed_password = get_password_hash(user_in.password)

    db.commit()
    db.refresh(user)
    return user


@admin_router.put(
    "/users/{user_id}/roles",
    response_model=UserOut,
    summary="Asignar/quitar roles a un usuario",
)
async def update_user_roles(
    user_id: str,
    patch: UserRolePatch,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
):
    """
    Modificar los roles de un usuario mediante add/remove (lista de IDs de rol).
    Auto-protección: un admin no puede quitarse a sí mismo el rol admin.
    """
    user = _get_user_or_404(db, user_id)

    current_role_ids = {r.id for r in user.roles}

    # Validar que los roles a agregar existan
    add_ids = set(patch.add)
    if add_ids:
        roles_to_add = db.query(Role).filter(Role.id.in_(add_ids)).all()
        if len(roles_to_add) != len(add_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más roles a agregar no existen",
            )
        current_role_ids |= add_ids

    current_role_ids -= set(patch.remove)

    # Auto-protección: el admin no puede quitarse su propio rol admin
    admin_role = (
        db.query(Role).filter(func.lower(Role.rol) == "admin").first()
    )
    if (
        admin_role
        and user.id == current_user["id"]
        and admin_role.id in set(patch.remove)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede quitarse a sí mismo el rol de administrador",
        )

    user.roles = db.query(Role).filter(Role.id.in_(current_role_ids)).all()
    db.commit()
    db.refresh(user)
    return user


@admin_router.patch(
    "/users/{user_id}/status",
    response_model=UserOut,
    summary="Activar o desactivar un usuario",
)
async def set_user_status(
    user_id: str,
    is_active: bool = Query(..., description="Nuevo estado de activación"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("users:status")),
):
    """
    Activar/desactivar un usuario de forma explícita (idempotente).
    Auto-protección: un admin no puede desactivarse a sí mismo.
    """
    user = _get_user_or_404(db, user_id)
    if user.id == current_user["id"] and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivarse a sí mismo",
        )
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@admin_router.get("/audit-logs", description="Obtener registros de auditoría")
async def get_audit_logs(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("audit:read")),
    action: str | None = Query(
        None, description="Filtrar por acción (USER_LOGIN, USER_REGISTER, etc.)"
    ),
    user_id: str | None = Query(None, description="Filtrar por ID de usuario"),
    days: int = Query(7, description="Días hacia atrás a consultar (default: 7)"),
    limit: int = Query(100, description="Límite de registros (default: 100, max: 500)"),
):
    """
    Obtener registros de auditoría (Sólo para Administradores).

    Permite filtrar por:
    - action: tipo de acción (USER_LOGIN, USER_REGISTER, PASSWORD_CHANGE, etc.)
    - user_id: ID del usuario específico
    - days: cantidad de días hacia atrás
    - limit: cantidad máxima de registros
    """
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
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
