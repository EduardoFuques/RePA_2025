from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from src.models.user_models import User
from src.schemas.user_schemas import UserUpdate
from src.database import get_db
from src.logger import logger
from src.token_utils import decode_access_token, decode_refresh_token
import re

# Objeto necesario para la función de 'get_current_user' que valida los datos del usuario
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

# Configuración de passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashear la contraseña
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Actualizar último acceso... Esto se debe integrar a la ruta de logín del usuario.
def update_last_login(email: str, db: Session = Depends(get_db), description="Actualiza en el registro de usuario, fecha y hora del login."):
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
async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Valida el token de acceso y retorna los datos del usuario.
    """

    payload = decode_access_token(token)
    logger.debug(f"get_current_user - payload: {payload}")
    
    user_data = {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "roles": payload.get("roles"),
        "type": payload.get("type")
    }
    logger.debug(f"get_current_user - user_data: {user_data}")
    return user_data

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
    logger.debug(f"has_user_role - current_user: {current_user}")
    
    # Extraer los nombres de los roles del usuario en minúsculas
    user_roles = {role["rol"].lower() for role in current_user.get("roles", [])}
    logger.debug(f"has_user_role - user_roles: {user_roles}")
    # Convertir los roles requeridos a minúsculas para comparación insensible a mayúsculas/minúsculas
    required_roles_lower = {role.lower() for role in required_roles}
    logger.debug(f"has_user_role - required_roles_lower: {required_roles_lower}")
    
    hsa_role = user_roles.isdisjoint(required_roles_lower)
    logger.debug(f"has_user_role - hsa_role: {hsa_role}")
    
    # Verificar si hay intersección entre los roles del usuario y los roles requeridos
    return not user_roles.isdisjoint(required_roles_lower)

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
            detail="El correo electrónico ya está registrado por otro usuario"
        )
