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

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from src.audit import audit_log
from src.database import get_db
from src.models.audit_model import AuditAction, AuditLog
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
from src.search import filtro_texto
from src.utils import (
    get_password_hash,
    get_user_permissions,
    require_permissions,
    validar_password,
    verify_email_unique,
)

admin_router = APIRouter()


def _resolve_permissions(
    db: Session, codes: list[str], current_user: dict | None = None
) -> list[Permission]:
    """Resuelve códigos de permiso a entidades Permission; valida que existan.

    Si se pasa `current_user`, exige además que quien ejecuta ya posea todos
    los permisos que está intentando asignar (regla estándar de no-escalada).

    Por qué hace falta: `update_user_roles` protege el rol admin **por nombre**
    —solo un admin puede otorgarlo o quitarlo—, pero nada impedía que alguien
    con `roles:manage` creara un rol nuevo con el catálogo completo de permisos
    y se lo adjudicara: un admin en todo menos en la etiqueta. Hoy solo el rol
    admin tiene `roles:manage`, así que no era explotable; lo sería el día que
    ese permiso se delegue, que es exactamente cuando nadie se acuerda de esto.
    """
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

    if current_user is not None:
        propios = get_user_permissions(db, current_user)
        ajenos = set(unique_codes) - propios
        if ajenos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No puede asignar permisos que usted no posee: "
                    f"{', '.join(sorted(ajenos))}"
                ),
            )

    return perms


def _rechazar_si_es_rol_del_sistema(role: Role) -> None:
    """Los permisos de los roles del sistema se definen en rbac.py, no por API.

    `update_role` bloqueaba el *renombre* de un rol del sistema pero dejaba
    pasar el cambio de permisos. El cambio se guardaba, la UI decía que había
    salido bien, y en el siguiente arranque `sync_rbac` (seed.py) reasignaba
    los permisos desde rbac.py y lo revertía. Sin ningún aviso.
    """
    if role.is_system or role.rol.lower() in SYSTEM_ROLE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Los permisos de un rol del sistema se definen en el código "
                "(src/rbac.py) y se re-sincronizan en cada arranque, así que un "
                "cambio hecho acá se perdería. Para otra combinación de "
                "permisos, creá un rol nuevo."
            ),
        )


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
@admin_router.get("/roles", response_model=list[RoleDetailOut], summary="Listar roles")
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
):
    """Crear un nuevo rol con permisos granulares."""
    nombre = data.rol.strip()
    if not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del rol es obligatorio",
        )
    existing = db.query(Role).filter(func.lower(Role.rol) == nombre.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un rol con ese nombre",
        )
    role = Role(rol=nombre, descripcion=data.descripcion, is_system=False)
    role.permissions = _resolve_permissions(db, data.permissions, current_user)
    db.add(role)
    db.commit()
    db.refresh(role)
    audit_log(
        db=db,
        action=AuditAction.CREATE,
        user_id=current_user["id"],
        resource_type="Role",
        resource_id=str(role.id),
        details={"rol": role.rol, "permissions": data.permissions},
        request=request,
    )
    db.commit()
    return role


@admin_router.put(
    "/roles/{role_id}", response_model=RoleDetailOut, summary="Actualizar un rol"
)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
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
        _rechazar_si_es_rol_del_sistema(role)
        role.permissions = _resolve_permissions(db, data.permissions, current_user)

    db.commit()
    db.refresh(role)
    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="Role",
        resource_id=str(role.id),
        details={"rol": role.rol},
        request=request,
    )
    db.commit()
    return role


@admin_router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un rol",
)
async def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
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
    rol_nombre = role.rol
    db.delete(role)
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="Role",
        resource_id=str(role_id),
        details={"rol": rol_nombre},
        request=request,
    )
    db.commit()
    return None


@admin_router.get(
    "/users",
    summary="Listar usuarios (paginado y filtrable)",
    responses={
        200: {"description": "{items, total, offset, limit}"},
        403: {"description": "No autorizado (requiere rol admin)"},
    },
)
async def get_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("users:read")),
    search: str | None = Query(None, description="Búsqueda por email (ignora acentos)"),
    role: str | None = Query(None, description="Filtrar por nombre de rol"),
    is_active: bool | None = Query(None, description="Filtrar por estado de la cuenta"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Listar usuarios con paginación y filtros.

    Antes devolvía `db.query(User).all()` sin límite y el frontend filtraba en
    memoria: con el padrón creciendo eso deja de servir, y la búsqueda no veía
    los usuarios que no estaban en la página.

    Devuelve `{items, total, offset, limit}` para poder paginar del lado del
    cliente sabiendo cuántas páginas hay.
    """
    query = db.query(User)

    if search and search.strip():
        query = query.filter(filtro_texto(db, [User.email], search.strip()))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    if role:
        query = query.filter(User.roles.any(Role.rol == role))

    total = query.count()
    usuarios = (
        query.options(selectinload(User.persona_fisica))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # `tiene_persona_fisica`: para designar admin hace falta ya tener un
    # registro de Persona Física (ver update_user_roles) — se muestra acá
    # para que Administradores.jsx pueda avisarlo antes de intentarlo.
    items = []
    for u in usuarios:
        item = UserOut.model_validate(u).model_dump()
        item["tiene_persona_fisica"] = u.persona_fisica is not None
        items.append(item)

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("users:write")),
):
    """Modificar email y/o contraseña de un usuario.

    Deja auditoría: un admin cambiando el email o la contraseña de otra cuenta
    es exactamente el tipo de acción que hay que poder reconstruir después, y
    hasta acá era el único endpoint sensible que no registraba nada.
    """
    user = _get_user_or_404(db, user_id)

    cambios = []
    email_anterior = user.email

    if user_in.email and user_in.email != user.email:
        # Validar unicidad de email para evitar IntegrityError 500
        verify_email_unique(db, user_in, {"id": user.id, "email": user.email})
        user.email = user_in.email
        cambios.append("email")
    if user_in.password:
        validar_password(user_in.password)
        user.hashed_password = get_password_hash(user_in.password)
        cambios.append("password")

    if not cambios:
        return user

    db.commit()
    db.refresh(user)

    # Nunca la contraseña, ni vieja ni nueva: solo que se cambió.
    detalles = {"campos": cambios, "email": user.email}
    if "email" in cambios:
        detalles["email_anterior"] = email_anterior
    audit_log(
        db=db,
        action=AuditAction.PASSWORD_CHANGE
        if cambios == ["password"]
        else AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="User",
        resource_id=user.id,
        details=detalles,
        request=request,
    )
    db.commit()
    return user


@admin_router.put(
    "/users/{user_id}/roles",
    response_model=UserOut,
    summary="Asignar/quitar roles a un usuario",
)
async def update_user_roles(
    user_id: str,
    patch: UserRolePatch,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("roles:manage")),
):
    """
    Modificar los roles de un usuario mediante add/remove (lista de IDs de rol).
    Auto-protección: un admin no puede quitarse a sí mismo el rol admin.
    """
    user = _get_user_or_404(db, user_id)

    original_role_ids = {r.id for r in user.roles}
    current_role_ids = set(original_role_ids)

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

    admin_role = db.query(Role).filter(func.lower(Role.rol) == "admin").first()
    admin_afectado = admin_role and admin_role.id in (
        set(patch.add) | set(patch.remove)
    )

    # Solo un admin puede otorgar o quitar el rol admin. El permiso
    # roles:manage alcanza para los demás roles, pero no para escalar
    # a (o degradar de) administrador.
    if admin_afectado:
        current_roles = {r["rol"].lower() for r in (current_user.get("roles") or [])}
        if "admin" not in current_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un administrador puede otorgar o quitar el rol admin",
            )

    # Para ser designado administrador hay que ya estar en la plataforma:
    # tener un registro de Persona Física en el Padrón. No aplica si el
    # usuario ya era admin (ej. patch que solo toca otros roles). Va
    # DESPUÉS del chequeo de permisos de arriba: quién puede intentarlo
    # importa antes que si el objetivo califica.
    if (
        admin_role
        and admin_role.id in add_ids
        and admin_role.id not in original_role_ids
        and user.persona_fisica is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un registro de Persona Física en el Padrón. "
            "Para ser administrador primero tiene que completar su registro RePA.",
        )

    # Auto-protección: el admin no puede quitarse su propio rol admin
    if (
        admin_role
        and user.id == current_user["id"]
        and admin_role.id in set(patch.remove)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede quitarse a sí mismo el rol de administrador",
        )

    # Protección de último admin: no dejar el sistema sin ningún
    # administrador activo.
    if (
        admin_role
        and admin_role.id in set(patch.remove)
        and admin_role.id not in set(patch.add)
    ):
        otros_admins_activos = (
            db.query(User)
            .filter(
                User.id != user.id,
                User.is_active.is_(True),
                User.roles.any(Role.id == admin_role.id),
            )
            .count()
        )
        if otros_admins_activos == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede quitar el rol admin al último administrador activo",
            )

    user.roles = db.query(Role).filter(Role.id.in_(current_role_ids)).all()
    db.commit()
    db.refresh(user)
    audit_log(
        db=db,
        action=AuditAction.ROLE_CHANGE,
        user_id=current_user["id"],
        resource_type="User",
        resource_id=user.id,
        details={"add": list(patch.add), "remove": list(patch.remove)},
        request=request,
    )
    db.commit()
    return user


@admin_router.patch(
    "/users/{user_id}/status",
    response_model=UserOut,
    summary="Activar o desactivar un usuario",
)
async def set_user_status(
    user_id: str,
    request: Request,
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
    # Protección de último admin: desactivar al último administrador activo
    # dejaría el sistema sin administración.
    if not is_active:
        admin_role = db.query(Role).filter(func.lower(Role.rol) == "admin").first()
        if admin_role and any(r.id == admin_role.id for r in user.roles):
            otros_admins_activos = (
                db.query(User)
                .filter(
                    User.id != user.id,
                    User.is_active.is_(True),
                    User.roles.any(Role.id == admin_role.id),
                )
                .count()
            )
            if otros_admins_activos == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede desactivar al último administrador activo",
                )
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    audit_log(
        db=db,
        action=AuditAction.ACTIVATE if is_active else AuditAction.DEACTIVATE,
        user_id=current_user["id"],
        resource_type="User",
        resource_id=user.id,
        request=request,
    )
    db.commit()
    return user


@admin_router.get(
    "/audit-actions",
    description="Listar los tipos de acción de auditoría posibles (para poblar un filtro)",
)
async def list_audit_actions(
    _: dict = Depends(require_permissions("audit:read")),
):
    """Catálogo de acciones de auditoría conocidas, para un filtro tipo desplegable."""
    canonicas = [
        v
        for k, v in vars(AuditAction).items()
        if not k.startswith("_") and isinstance(v, str)
    ]
    # USER_REGISTER / USER_LOGIN son strings ad-hoc usados hoy en user_routes.py,
    # no forman parte de las constantes canónicas de AuditAction pero sí aparecen
    # en los logs reales — se listan aparte para que el filtro los cubra también.
    return sorted(set(canonicas) | {"USER_REGISTER", "USER_LOGIN"})


@admin_router.get("/audit-logs", description="Obtener registros de auditoría")
async def get_audit_logs(
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("audit:read")),
    action: str | None = Query(
        None, description="Filtrar por acción (USER_LOGIN, USER_REGISTER, etc.)"
    ),
    actions: list[str] | None = Query(
        None,
        description=(
            "Filtrar por varias acciones a la vez. Sirve para feeds que solo "
            "quieren acciones con significado (creaciones, cambios de rol…) y "
            "no el ruido de los logins."
        ),
    ),
    user_id: str | None = Query(None, description="Filtrar por ID de usuario"),
    email: str | None = Query(
        None,
        description=(
            "Filtrar por email del usuario. Evita tener que pegar un UUID a mano, "
            "que era la única forma de filtrar por persona."
        ),
    ),
    resource_type: str | None = Query(
        None, description="Filtrar por tipo de recurso (User, Role, PersonaFisica…)"
    ),
    resource_id: str | None = Query(None, description="Filtrar por ID de recurso"),
    request_id: str | None = Query(
        None,
        description=(
            "Todas las acciones de una misma request HTTP. Es el mismo valor que "
            "aparece en la línea de log canónico de esa request."
        ),
    ),
    desde: datetime | None = Query(None, description="Fecha/hora mínima (ISO)"),
    hasta: datetime | None = Query(None, description="Fecha/hora máxima (ISO)"),
    days: int = Query(7, description="Días hacia atrás (se ignora si se pasa `desde`)"),
    limit: int = Query(
        100, description="Límite de registros por página (default: 100, max: 500)"
    ),
    offset: int = Query(
        0, ge=0, description="Desplazamiento para paginación (default: 0)"
    ),
):
    """
    Obtener registros de auditoría, paginados (Sólo para Administradores).

    Permite filtrar por:
    - action: tipo de acción (USER_LOGIN, USER_REGISTER, PASSWORD_CHANGE, etc.)
    - user_id: ID del usuario específico
    - days: cantidad de días hacia atrás
    - limit / offset: paginación

    Devuelve {items, total, offset, limit} — `total` es el conteo total de
    registros que matchean los filtros (sin paginar), para que el frontend
    pueda calcular cuántas páginas hay.
    """
    # Limitar el máximo de registros por página
    limit = min(limit, 500)

    # `desde` explícito gana sobre la ventana de días.
    start_date = desde or (datetime.now(timezone.utc) - timedelta(days=days))

    # Construir query
    query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)
    if hasta:
        query = query.filter(AuditLog.created_at <= hasta)

    if action:
        query = query.filter(AuditLog.action == action)
    if actions:
        query = query.filter(AuditLog.action.in_(actions))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if email and email.strip():
        query = query.filter(
            AuditLog.user_id.in_(
                db.query(User.id).filter(filtro_texto(db, [User.email], email.strip()))
            )
        )
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    if request_id:
        query = query.filter(AuditLog.request_id == request_id)

    total = query.count()

    # Ordenar por fecha descendente y paginar
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    # El UUID del usuario no le dice nada a quien lee la auditoría: se resuelve
    # el email en un solo query por página (no uno por fila).
    ids = {log.user_id for log in logs if log.user_id}
    emails: dict[str, str] = {}
    if ids:
        emails = {
            u.id: u.email
            for u in db.query(User.id, User.email).filter(User.id.in_(ids)).all()
        }

    return {
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "user_email": emails.get(log.user_id),
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "request_id": log.request_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
