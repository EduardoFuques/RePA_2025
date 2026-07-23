from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# Esquema para Permisos
class PermissionOut(BaseModel):
    id: int
    code: str
    descripcion: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Esquema para Roles
class RoleBase(BaseModel):
    rol: str


class RoleOut(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Esquema detallado de rol (incluye permisos y metadatos)
class RoleDetailOut(RoleBase):
    id: int
    descripcion: str | None = None
    is_system: bool = False
    permissions: list[PermissionOut] = []

    model_config = ConfigDict(from_attributes=True)


# Esquema para crear un rol
class RoleCreate(BaseModel):
    rol: str
    descripcion: str | None = None
    # Lista de códigos de permiso (ej. ["users:read", "audit:read"])
    permissions: list[str] = []


# Esquema para actualizar un rol
class RoleUpdate(BaseModel):
    rol: str | None = None
    descripcion: str | None = None
    permissions: list[str] | None = None


# Esquemas de usuario
class UserBase(BaseModel):
    email: EmailStr


# Esquema para creación de usuario
class UserCreate(UserBase):
    password: str  # Contraseña en texto plano (se hasheará en el backend)
    roles: list[int] | None = [2]  # Lista de IDs de roles asignados


# Esquema para salida de usuario
class UserOut(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None
    roles: list[RoleOut] = []

    model_config = ConfigDict(from_attributes=True)


# Esquema para actualización de usuario
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None  # Nueva contraseña (se hasheará)


# Esquema para confirmar acción con contraseña
class PasswordConfirm(BaseModel):
    password: str


# Esquema para actualizar roles de usuario
class UserRolePatch(BaseModel):
    add: list[int] = []
    remove: list[int] = []


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# Esquema para Recuperacion de Usuario
class TokenData(BaseModel):
    user_id: str
    token_data: str = None


# Esquema para Base de datos de TokenRecovery
class TokenDB(TokenData):
    id: str
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool


# Esquema para metadata de formularios del usuario
class UserFormsMetadata(BaseModel):
    has_pf: bool = False
    has_pj: bool = False
    has_as: bool = False
    has_esa: bool = False
    has_agam: bool = False
    has_sala: bool = False
    has_exhibicion: bool = False
    has_festival: bool = False
