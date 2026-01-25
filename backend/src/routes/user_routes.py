from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from src.models.user_models import User, Role, TokenRecovery
from src.schemas.user_schemas import UserCreate, UserOut, UserUpdate, TokenData, TokenDB
from src.database import get_db
from src.utils import get_password_hash,validar_password,update_last_login,get_current_user
from src.token_utils import create_access_token, decode_access_token
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()

URL_SITE = os.getenv("URL_SITE")
SECRET_KEY = os.getenv("SECRET_KEY") # Cambia esto a un valor seguro
ALGORITHM = os.getenv("ALGORITHM")

user_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear un usuario nuevo# Crear un usuario nuevo
@user_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED ,description="Crear un nuevo usuario")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registrar un nuevo usuario con el rol "user" por defecto.
    
    Args:
        user_in (UserCreate): Datos del usuario a crear.
    Return:
        new_user (UserOut): Usuario Creado.
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
        expires_delta=1440  # 24 horas en minutos
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
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error en el registro de New User"
        )
    # TODO: Implementar envío de email en producción
    verification_url = f"{URL_SITE}/users/confirm/{registration_token}"
    
    return new_user # Retorna el usuario creado{"detail": "Registro exitoso. Verifica tu email"}

# 2. Endpoint de Verificación
@user_router.post("/confirm/{token}", status_code=status.HTTP_201_CREATED, description="Verificar el token de registro")
async def confirm_registration(token: str, db: Session = Depends(get_db)):
    """
    Verificar el token de registro y activar el usuario.
    Args:
        token (str): Token de verificación.
    """
    # Validar si existe el token, y está activo
    token_record = db.query(TokenRecovery).filter(token == TokenRecovery.token_payload, TokenRecovery.is_active == True).first()
    if token_record is None:
        raise HTTPException(status_code=404, detail="Token no encontrado o inactivo")
    
    try:

        # Verificar token
        payload = decode_access_token(token)
        
        # Validaciones críticas
        if payload.get("type") != "access" or "unverified" not in payload.get("roles", []):
            raise HTTPException(status_code=400, detail="Token inválido")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Activar usuario y eliminar token
        user.is_active = True
        db.query(TokenRecovery).filter(
            TokenRecovery.token_payload == token,
            TokenRecovery.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        return {"detail": "Cuenta verificada exitosamente"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")

# Inicio de sesión [form_data: OAuth2PasswordRequestForm = Depends()]
@user_router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Iniciar sesión con un usuario registrado.
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
    
    # Actualizar la fecha y hora del último acceso
    update_last_login(user.email, db)
    
    # Convertir usuario a formato UserOut compatible con JSON
    data_access = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "roles": [{"id": role.id, "rol": role.rol} for role in user.roles],
        "type": "access"
    }
    
    data_refresh = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "roles": [{"id": role.id, "rol": role.rol} for role in user.roles],
        "type": "refresh"
    }

    # Generar un token de acceso
    #access_token = create_access_token(data=data_access)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "roles": [{"id": role.id, "rol": role.rol} for role in user.roles]},
        expires_delta=1440  # 24 horas en minutos
    )
    # refresh_token = create_refresh_token(data=data_refresh)
    refresh_token = create_access_token(
        data={"sub": user.id, "email": user.email, "roles": [{"id": role.id, "rol": role.rol} for role in user.roles], "type": "refresh"},
        expires_delta=(60*24*7)  # 7 dias, en minutos
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

# Generar el Token de Recover Password
@user_router.put("/recovery_passwd", response_model=UserUpdate, description="Generar el Token de Recover Password")
async def recovery_passwd_user(user_in: UserUpdate, db: Session = Depends(get_db)):
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
    user= db.query(User).filter(User.email == user_in.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario no existe")
    validar_password(user_in.password)
    hashed_password = get_password_hash(user_in.password)
    # Generar token de registro (24h de validez)
    registration_token = create_access_token(
        data={"sub": user.id, "new_password": hashed_password},
        expires_delta=1440  # 24 horas en minutos
    )
    
    # Guardar token de recuperación
    recovery_record = TokenRecovery(
        user_id=user.id,
        token_payload=registration_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1440),
    )
    
    # Guardar el nuevo usuario y el token de recuperación en la base de datos
    try:
        db.add(recovery_record)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error en el registro de Token Recovery"
        )
    # TODO: Implementar envío de email en producción
    verification_url = f"{URL_SITE}/users/recovery/{registration_token}"
    
    return user # Retorna el usuario 

# Recuperar la contraseña del usuario
@user_router.get("/recovery/{token}", response_model=UserOut, description="Recuperar la contraseña del usuario")
async def recovery_passwd(token: str, db: Session = Depends(get_db)):
    """
    Recuperar la contraseña del usuario.
    Args:
        token (string): Token de recuperación
    """
    # Verificar token
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario no existe")
    # Actualizar la contraseña del usuario
    user.hashed_password = payload.get("new_password")
    db.commit()
    db.refresh(user)
    # Eliminar el token de recuperación
    db.query(TokenRecovery).filter(TokenRecovery.user_id == user_id).delete()
    db.commit() 

    return user

# Obtener los datos del usuario actual
@user_router.get("/me", response_model=UserOut, description="Obtener datos del usuario actual")
async def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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

# Actualizar usuario
@user_router.put("/me", response_model=UserUpdate, description="Actualizar los datos del usuario actual")
async def update_user(user_in: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Actualizar los datos del usuario actual.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["sub"]).first()
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

# Eliminar usuario
@user_router.delete("/me", description="Eliminar el usuario actual")
async def delete_user(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Cambiar estado de is_active True/False.
    """
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    # Guardar los cambios
    db.commit()
    db.refresh(user)
    #return {"message": "Usuario eliminado"}
    return user