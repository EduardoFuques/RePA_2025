import re
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config import REPA_GATING_ENABLED
from src.database import get_db
from src.logger import logger
from src.models.persona_fisica_model import PersonaFisica
from src.models.registro_lifecycle import EstadoRegistro
from src.models.user_models import Role, User
from src.rbac import ALL_PERMISSIONS
from src.schemas.user_schemas import UserUpdate
from src.token_utils import decode_access_token

# Objeto necesario para la función de 'get_current_user' que valida los datos del usuario
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

# Configuración de passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hashear la contraseña
def get_password_hash(password: str):
    return pwd_context.hash(password)


# Actualizar último acceso... Esto se debe integrar a la ruta de logín del usuario.
def update_last_login(
    email: str,
    db: Session = Depends(get_db),
    description="Actualiza en el registro de usuario, fecha y hora del login.",
):
    """
    Actualiza en el registro de usuario, fecha y hora del login.
    """
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_user)
    return db_user


# Validar el usuario
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Valida el token de acceso y retorna los datos del usuario.

    Revalida contra la base en cada request: el JWT es stateless y, sin este
    chequeo, un usuario desactivado (o al que se le quitó un rol) seguiría
    operando con su token vigente hasta que expire. Los roles se toman de la
    DB, no del token, para que un cambio de roles surta efecto inmediato.
    """

    payload = decode_access_token(token)

    db_user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o inexistente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_revocado(db_user, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada, volvé a iniciar sesión",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = {
        "id": db_user.id,
        "email": db_user.email,
        "roles": [{"id": r.id, "rol": r.rol} for r in db_user.roles],
        "type": payload.get("type"),
    }
    # No registrar el payload completo para evitar fuga de PII en logs
    logger.debug(f"get_current_user - user_id: {user_data['id']}")
    return user_data


def token_revocado(db_user: User, payload: dict) -> bool:
    """Indica si el token pertenece a una generacion de sesiones ya revocada.

    Cada token lleva en el claim `tv` la version que tenia el usuario cuando se
    emitio. Cambiar la contrasena la incrementa, con lo cual todo token anterior
    deja de valer — que es lo que permite que un cambio de clave expulse a una
    sesion robada (ver AUT-03).

    Se usa un contador y no una marca de tiempo porque el `iat` de un JWT tiene
    resolucion de un segundo: con timestamps es imposible distinguir el token
    emitido justo antes del cambio del que se emite justo despues, al volver a
    loguearse. Con un contador no hay ventana ambigua.

    Los tokens emitidos antes de este cambio no traen `tv`; se los acepta para
    no desloguear a todo el mundo en el deploy. Cuando expiren (30 minutos los
    de acceso, 7 dias los de refresco) el hueco se cierra solo.
    """
    tv_token = payload.get("tv")
    if tv_token is None:
        return False
    return int(tv_token) != int(db_user.token_version or 0)


def revocar_sesiones(db_user: User) -> None:
    """Invalida todos los tokens vigentes del usuario.

    Se llama al cambiar la contrasena. Incrementar la version deja fuera a todo
    token emitido antes, sin la ventana ambigua que tendria una comparacion por
    tiempo (ver token_revocado).
    """
    db_user.token_version = (db_user.token_version or 0) + 1


def validar_password(password: str):
    """
    Valida que la contraseña cumpla con los requisitos:
    - Mínimo 8 caracteres.
    - Al menos una letra mayúscula.
    - Al menos un número.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres",
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra mayúscula",
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número",
        )


# Verifica si el usuario tiene al menos uno de los roles requeridos
def has_user_role(current_user: dict, required_roles: list[str]) -> bool:
    """
    Verifica si el usuario tiene al menos uno de los roles requeridos.

    Args:
        current_user (dict): Diccionario con los datos del usuario (incluyendo 'roles')
        required_roles (list[str]): Lista de roles requeridos (ej. ["admin", "editor"])

    Returns:
        bool: True si tiene al menos un rol requerido, False en caso contrario
    """
    # Extraer los nombres de los roles del usuario en minúsculas
    user_roles = {role["rol"].lower() for role in (current_user.get("roles") or [])}
    # Comparación insensible a mayúsculas/minúsculas
    required_roles_lower = {role.lower() for role in required_roles}

    # Verificar si hay intersección entre los roles del usuario y los requeridos
    return not user_roles.isdisjoint(required_roles_lower)


def get_user_role_names(current_user: dict) -> set[str]:
    """Devuelve el conjunto de nombres de rol del usuario (en minúsculas)."""
    return {role["rol"].lower() for role in (current_user.get("roles") or [])}


def get_user_permissions(db: Session, current_user: dict) -> set[str]:
    """
    Resuelve el conjunto de permisos efectivos de un usuario a partir de sus roles.
    El rol 'admin' obtiene todos los permisos del sistema.
    """
    role_names = get_user_role_names(current_user)
    if "admin" in role_names:
        return set(ALL_PERMISSIONS)

    if not role_names:
        return set()

    roles = db.query(Role).filter(func.lower(Role.rol).in_(role_names)).all()
    perms: set[str] = set()
    for role in roles:
        perms.update(p.code for p in role.permissions)
    return perms


def require_roles(*roles: str):
    """
    Factory de dependencia FastAPI que exige que el usuario tenga al menos
    uno de los roles indicados. Uso: Depends(require_roles("admin")).
    """

    async def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        if not has_user_role(current_user, list(roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción",
            )
        return current_user

    return _checker


def require_permissions(*codes: str):
    """
    Factory de dependencia FastAPI que exige que el usuario posea TODOS los
    permisos indicados (resueltos desde sus roles). Uso:
    Depends(require_permissions("users:read")).
    """

    async def _checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        user_perms = get_user_permissions(db, current_user)
        if not set(codes).issubset(user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene los permisos requeridos para esta acción",
            )
        return current_user

    return _checker


async def require_pf_aprobado(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Dependencia de gating del Padrón RePA.

    Exige que el usuario tenga su Persona Física (PF) enviada (con código RePA
    emitido) para poder crear el resto de los registros (PJ, AS, AGAM, Sala,
    Festival, Exhibición). ESA queda fuera (pista cerrada).

    NOTA: antes exigía específicamente estado ``aprobado``. El código RePA
    ahora se emite en el envío del formulario, no en la aprobación admin (el
    circuito de aprobación es post-lanzamiento) — exigir "aprobado" acá
    dejaría a todo el mundo bloqueado indefinidamente. Alcanza con que la PF
    haya salido de "borrador" (tiene código emitido).

    Controlada por ``REPA_GATING_ENABLED`` (default OFF): mientras esté desactivada, la
    dependencia es transparente. Se activará junto con el onboarding del frontend.
    """
    if not REPA_GATING_ENABLED:
        return current_user

    pf = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if pf is None or pf.estado == EstadoRegistro.borrador.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Necesitás enviar tu Persona Física (PF) en el Padrón RePA "
                "antes de registrar esta entidad."
            ),
        )
    return current_user


# Verifica que el usuario tenga rol de administrador
def check_any_permission(db: Session, current_user: dict, *codes: str):
    """
    Verifica que el usuario posea AL MENOS UNO de los permisos indicados
    (el rol admin los tiene todos). Variante "OR" de check_permissions, para
    endpoints compartidos por más de un rol de gestión (p. ej. comités y
    dictámenes de fomento, operados tanto por gestor_fomento como por
    evaluador). Lanza HTTPException 403 si no tiene ninguno.
    """
    user_perms = get_user_permissions(db, current_user)
    if not user_perms.intersection(codes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene los permisos requeridos para esta acción",
        )


def check_permissions(db: Session, current_user: dict, *codes: str):
    """
    Verifica que el usuario posea TODOS los permisos indicados (el rol admin
    los tiene todos). Variante imperativa de require_permissions para rutas
    que ya reciben current_user/db — permite que roles como gestor_fomento
    o evaluador operen endpoints de gestión sin necesitar el rol admin.
    Lanza HTTPException 403 si falta alguno.
    """
    user_perms = get_user_permissions(db, current_user)
    if not set(codes).issubset(user_perms):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene los permisos requeridos para esta acción",
        )


# Verifica que el nuevo email no esté siendo usado por otro usuario
def verify_email_unique(db: Session, user_in: UserUpdate, current_user: dict):
    """
    Verifica que el nuevo email no esté siendo usado por otro usuario
    y que no pertenezca al usuario actual
    """
    # Si el email no cambió, no es necesario verificar
    if user_in.email == current_user["email"]:
        return

    # Buscar usuario con el email propuesto
    existing_user = db.query(User).filter(User.email == user_in.email).first()

    # Si existe y pertenece a otro usuario, lanzar error
    if existing_user and existing_user.id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado por otro usuario",
        )
