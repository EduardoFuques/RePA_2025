"""
Rutas de usuarios: registro, login, recuperación de contraseña y gestión de perfil.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.audit import audit_log
from src.database import get_db
from src.models.user_models import Role, TokenRecovery, User
from src.rate_limiter import limiter
from src.schemas.user_schemas import (
    PasswordConfirm,
    UserCreate,
    UserFormsMetadata,
    UserOut,
    UserUpdate,
)
from src.token_utils import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from src.utils import (
    get_current_user,
    get_password_hash,
    get_user_permissions,
    update_last_login,
    validar_password,
)

user_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Crear un usuario nuevo
@user_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario. El usuario queda inactivo hasta verificar su email.",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"description": "Email ya registrado o contraseña inválida"},
        429: {"description": "Demasiados intentos (rate limit)"},
    },
)
@limiter.limit("10/minute")
def create_user(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registrar un nuevo usuario en el sistema RePA.

    El usuario se crea con estado **inactivo** y rol **user** por defecto.
    Se genera un token de verificación que debe ser confirmado via email.

    **Requisitos de contraseña:**
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    """

    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado",
        )

    # Validar la contraseña
    validar_password(user_in.password)

    # Hashear la contraseña
    hashed_password = get_password_hash(user_in.password)

    # Clave ID para le nuevo usuario, Generar un UUID único
    new_user_id = str(uuid4())

    # Crear el nuevo usuario
    new_user = User(
        id=new_user_id,
        email=user_in.email,
        is_active=False,
        hashed_password=hashed_password,
        created_at=datetime.now(timezone.utc),
    )

    # Asignar el rol "user" por defecto
    user_role = db.query(Role).filter(Role.rol == "user").first()

    if not user_role:
        # Si el rol "user" no existe, crearlo
        user_role = Role(rol="user")
        db.add(user_role)
        db.commit()
        db.refresh(user_role)

    # Asociar el rol al nuevo usuario
    new_user.roles.append(user_role)

    # Crear el token de Verificación de correo electrónico
    # Generar token de registro (24h de validez)
    registration_token = create_access_token(
        data={"sub": new_user_id, "roles": ["unverified"]},
        expires_delta=1440,  # 24 horas en minutos
        type="verify",
    )

    # Guardar token de recuperación
    recovery_record = TokenRecovery(
        user_id=new_user_id,
        token_payload=registration_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1440),
    )

    # Guardar el nuevo usuario y el token de recuperación en la base de datos
    try:
        db.add(new_user)
        db.add(recovery_record)
        db.commit()

        # Registrar en audit trail
        audit_log(
            db=db,
            action="USER_REGISTER",
            user_id=new_user_id,
            resource_type="User",
            resource_id=new_user_id,
            details={"email": user_in.email},
            request=request,
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error en el registro de New User",
        )
    # TODO: Implementar envío de email en producción
    # verification_url = f"{URL_SITE}/users/confirm/{registration_token}"

    response = {
        "id": new_user.id,
        "email": new_user.email,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at,
        "last_login": new_user.last_login,
        "roles": [{"id": role.id, "rol": role.rol} for role in new_user.roles],
        "message": "Registro exitoso. En producción recibirás un email de verificación.",
    }
    # Solo exponer el token en entornos no productivos para pruebas manuales
    from src.config import IS_PRODUCTION

    if not IS_PRODUCTION:
        response["verification_token"] = registration_token
    return response


# 2. Endpoint de Verificación
@user_router.post(
    "/confirm/{token}",
    status_code=status.HTTP_201_CREATED,
    description="Verificar el token de registro",
)
@limiter.limit("10/minute")
async def confirm_registration(
    request: Request, token: str, db: Session = Depends(get_db)
):
    """
    Verificar el token de registro y activar el usuario.
    Args:
        token (str): Token de verificación.
    """
    # Validar si existe el token, y está activo
    token_record = (
        db.query(TokenRecovery)
        .filter(token == TokenRecovery.token_payload, TokenRecovery.is_active.is_(True))
        .first()
    )
    if token_record is None:
        raise HTTPException(status_code=404, detail="Token no encontrado o inactivo")

    try:
        # Verificar token
        payload = decode_access_token(token)

        # Validaciones críticas: debe ser token de verificación con rol unverified
        if payload.get("type") != "verify" or "unverified" not in payload.get(
            "roles", []
        ):
            raise HTTPException(status_code=400, detail="Token inválido")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Activar usuario y eliminar token
        user.is_active = True
        db.query(TokenRecovery).filter(
            TokenRecovery.token_payload == token, TokenRecovery.is_active.is_(True)
        ).update({"is_active": False})

        db.commit()
        return {"detail": "Cuenta verificada exitosamente"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")


# Inicio de sesión
@user_router.post(
    "/token",
    summary="Iniciar sesión",
    description="Autenticar usuario y obtener tokens JWT",
    responses={
        200: {"description": "Login exitoso, retorna access_token y refresh_token"},
        400: {"description": "Credenciales inválidas"},
        429: {"description": "Demasiados intentos (rate limit: 5/minuto)"},
    },
)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Iniciar sesión con email y contraseña.

    Retorna un **access_token** (válido 30 min) y un **refresh_token** (válido 7 días).

    El access_token debe incluirse en el header `Authorization: Bearer <token>`
    para acceder a endpoints protegidos.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico o contraseña incorrectos",
        )

    # Verificar la contraseña
    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico o contraseña incorrectos",
        )

    # Verificar si el usuario está activo (email verificado)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta no está verificada. Por favor, revisa tu correo electrónico y confirma tu cuenta.",
        )

    # Actualizar la fecha y hora del último acceso
    update_last_login(user.email, db)

    # Generar token de acceso (30 minutos)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "roles": [{"id": role.id, "rol": role.rol} for role in user.roles],
        },
        expires_delta=30,  # 30 minutos
    )
    # Generar refresh token (7 días) — contiene solo sub y type para minimizar exposición de datos
    refresh_token = create_refresh_token(
        data={
            "sub": user.id,
        }
    )

    # Registrar login en audit trail
    audit_log(
        db=db,
        action="USER_LOGIN",
        user_id=user.id,
        resource_type="User",
        resource_id=user.id,
        details={"email": user.email},
        request=request,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Generar el Token de Recover Password
@user_router.put(
    "/recovery_passwd",
    description="Generar el Token de Recover Password",
)
@limiter.limit("3/minute")
async def recovery_passwd_user(
    request: Request, user_in: UserUpdate, db: Session = Depends(get_db)
):
    """
    Generar el Token de Recover Password.
    Generar una password aleatoria y enviarla al correo del usuario.
    Args:
        email (string): Email del usuario
        passwd (string): Password Nuevo del usuario
    Returns:
        dict: Token de acceso y refresh token
        URL: dirección de recovery password
    """
    # Respuesta genérica para no revelar si el email existe en el sistema
    generic_response = {
        "detail": "Si el email está registrado, recibirás instrucciones para restablecer tu contraseña."
    }

    user = db.query(User).filter(User.email == user_in.email).first()
    if not user:
        return generic_response

    validar_password(user_in.password)
    hashed_password = get_password_hash(user_in.password)
    # Generar token de recuperación (24h de validez)
    # NOTA: el hash de la nueva contraseña se almacena solo en TokenRecovery, nunca en el JWT
    registration_token = create_access_token(
        data={"sub": user.id},
        expires_delta=1440,  # 24 horas en minutos
        type="recover",
    )

    # Guardar token de recuperación (la nueva contraseña hasheada solo vive en la DB)
    recovery_record = TokenRecovery(
        user_id=user.id,
        token_payload=registration_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1440),
        new_password=hashed_password,
    )

    # Guardar el token de recuperación en la base de datos
    try:
        db.add(recovery_record)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error en el registro de Token Recovery",
        )
    # TODO: Implementar envío de email en producción
    # verification_url = f"{URL_SITE}/users/recovery/{registration_token}"

    return generic_response


# Recuperar la contraseña del usuario
@user_router.post(
    "/recovery/{token}",
    response_model=UserOut,
    description="Recuperar la contraseña del usuario",
)
async def recovery_passwd(token: str, db: Session = Depends(get_db)):
    """
    Recuperar la contraseña del usuario.
    Args:
        token (string): Token de recuperación
    """
    # Verificar token
    payload = decode_access_token(token)
    if payload.get("type") != "recover":
        raise HTTPException(status_code=400, detail="Token inválido")
    user_id = payload.get("sub")
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no existe"
        )
    # Buscar la nueva contraseña en el registro de recuperación (nunca en el JWT)
    recovery_record = (
        db.query(TokenRecovery)
        .filter(
            TokenRecovery.token_payload == token,
            TokenRecovery.is_active.is_(True),
        )
        .first()
    )
    if not recovery_record or not recovery_record.new_password:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    # Actualizar la contraseña del usuario
    user.hashed_password = recovery_record.new_password
    db.commit()
    db.refresh(user)
    # Invalidar el token de recuperación
    db.query(TokenRecovery).filter(TokenRecovery.token_payload == token).update(
        {"is_active": False}
    )
    db.commit()

    return user


# Obtener los datos del usuario actual
@user_router.get(
    "/me", response_model=UserOut, description="Obtener datos del usuario actual"
)
async def read_users_me(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Obtener los datos del usuario actual.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico o contraseña incorrectos",
        )
    return user


# Obtener los permisos efectivos del usuario actual
@user_router.get(
    "/me/permissions",
    response_model=list[str],
    description="Obtener los permisos efectivos del usuario actual",
)
async def read_my_permissions(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Devuelve la lista de códigos de permiso efectivos del usuario."""
    return sorted(get_user_permissions(db, current_user))


# Obtener metadata de formularios del usuario
@user_router.get(
    "/me/forms",
    response_model=UserFormsMetadata,
    description="Obtener qué formularios tiene el usuario",
)
async def get_user_forms_metadata(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Obtener metadata de qué formularios tiene completados el usuario.
    Esto permite al frontend saber qué datos cargar sin hacer múltiples peticiones.
    """
    from src.models.asociacion_model import Asociacion
    from src.models.esa_model import EstudianteESA
    from src.models.exhibicion_model import Exhibicion, Festival, Sala
    from src.models.obra_audiovisual_model import ObraAudiovisual
    from src.models.persona_fisica_model import PersonaFisica
    from src.models.persona_juridica_model import PersonaJuridica

    user_id = current_user["id"]

    return UserFormsMetadata(
        has_pf=db.query(PersonaFisica).filter(PersonaFisica.user_id == user_id).first()
        is not None,
        has_pj=db.query(PersonaJuridica)
        .filter(PersonaJuridica.user_id == user_id)
        .first()
        is not None,
        has_as=db.query(Asociacion).filter(Asociacion.user_id == user_id).first()
        is not None,
        has_esa=db.query(EstudianteESA).filter(EstudianteESA.user_id == user_id).first()
        is not None,
        has_agam=db.query(ObraAudiovisual)
        .filter(ObraAudiovisual.user_id == user_id)
        .first()
        is not None,
        has_sala=db.query(Sala).filter(Sala.user_id == user_id).first() is not None,
        has_exhibicion=db.query(Exhibicion)
        .filter(Exhibicion.user_id == user_id)
        .first()
        is not None,
        has_festival=db.query(Festival).filter(Festival.user_id == user_id).first()
        is not None,
    )


# Actualizar usuario
@user_router.put(
    "/me",
    response_model=UserUpdate,
    description="Actualizar los datos del usuario actual",
)
async def update_user(
    user_in: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Actualizar los datos del usuario actual.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )

    # Actualizar los datos del usuario
    if user_in.email:
        user.email = (
            user_in.email
        )  # Actualizar el correo electrónico si se proporciona y no hay duplicados
    if user_in.password:
        validar_password(user_in.password)
        user.hashed_password = get_password_hash(user_in.password)

    # Guardar los cambios
    db.commit()
    db.refresh(user)

    # Devolver el usuario actualizado
    return user


# Eliminar usuario
@user_router.delete(
    "/me", description="Desactivar el usuario actual (requiere contraseña)"
)
async def delete_user(
    confirm: PasswordConfirm,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Desactivar la cuenta del usuario actual.
    Requiere la contraseña actual como confirmación de seguridad.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )

    # Verificar contraseña actual antes de desactivar
    if not pwd_context.verify(confirm.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña incorrecta",
        )

    user.is_active = False
    # Guardar los cambios
    db.commit()
    db.refresh(user)
    return user
