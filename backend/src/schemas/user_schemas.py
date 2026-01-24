from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime

# Esquema para Roles
class RoleBase(BaseModel):
    rol: str

class RoleOut(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# Esquemas de usuario
class UserBase(BaseModel):
    email: EmailStr

# Esquema para creación de usuario
class UserCreate(UserBase):
    password: str  # Contraseña en texto plano (se hasheará en el backend)
    roles: Optional[List[int]] = [2]  # Lista de IDs de roles asignados

# Esquema para salida de usuario
class UserOut(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleOut] = []
    
    model_config = ConfigDict(from_attributes=True)

# Esquema para actualización de usuario
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # Nueva contraseña (se hasheará)

# Esquema para actualizar roles de usuario
class UserRolePatch(BaseModel):
    add: List[int] = []
    remove: List[int] = []

# Esquema para Recuperacion de Usuario
class TokenData(BaseModel):
    user_id: str
    token_data: str = None

# Esquema para Base de datos de TokenRecovery
class TokenDB(TokenData):
    id: str
    created_at:datetime
    expires_at: Optional[datetime] = None
    is_active: bool
