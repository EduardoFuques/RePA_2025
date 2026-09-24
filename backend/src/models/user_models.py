import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.database import Base


# Modelo para Token de Verificación de Correo
class TokenRecovery(Base):
    __tablename__ = "token_recovery"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    token_payload = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    new_password = Column(String, nullable=True)


# Modelo asociativa para la relación muchos a muchos entre usuarios y roles
class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))


# Tabla asociativa muchos-a-muchos entre roles y permisos
class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"))


# Modelo de Permiso (granularidad recurso:accion, ej. "users:read")
class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    descripcion = Column(String, nullable=True)


# Modelo de Role
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    rol = Column(String, unique=True, index=True, nullable=False)
    descripcion = Column(String, nullable=True)
    # Roles del sistema no pueden eliminarse ni renombrarse
    is_system = Column(Boolean, default=False, nullable=False)
    # Permisos asociados al rol
    permissions = relationship(
        "Permission", secondary="role_permissions", backref="roles"
    )
    # Relación inversa con usuarios definida en User


# Modelo de User
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "tipo_cuenta IN ('ciudadano', 'equipo')", name="ck_users_tipo_cuenta"
        ),
    )
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, default=None, nullable=True)
    # Generacion de sesiones. Cada token lleva el valor que tenia este campo
    # cuando se emitio; cambiar la contrasena lo incrementa y con eso caen
    # todas las sesiones abiertas, incluidos los refresh de 7 dias.
    #
    # Es un contador y no una marca de tiempo a proposito: el `iat` de un JWT
    # tiene resolucion de un segundo, asi que con timestamps no se puede
    # distinguir el token emitido justo antes del cambio del que se emite justo
    # despues, al volver a loguearse.
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    # ciudadano: autoregistro (user/estudiante). equipo: roles internos, alta
    # por un admin. Se fija al crear la cuenta; los roles se validan contra el.
    tipo_cuenta = Column(String(20), nullable=False, default="ciudadano")
    # Cuando la persona eligio su contrasena. NULL en una cuenta de equipo
    # recien creada = pendiente de activacion.
    password_definida_at = Column(DateTime, nullable=True)

    @property
    def pendiente_activacion(self) -> bool:
        """Cuenta del equipo cuya persona todavia no eligio contrasena."""
        return self.tipo_cuenta == "equipo" and self.password_definida_at is None

    # Relación con roles a través de la tabla UserRole
    roles = relationship("Role", secondary="user_roles", backref="users")

    # Relaciones con formularios RePA
    # foreign_keys explícito: cada entidad tiene además 'revisado_por' (2da FK a users)
    persona_fisica = relationship(
        "PersonaFisica",
        back_populates="user",
        uselist=False,
        foreign_keys="PersonaFisica.user_id",
    )  # 1:1
    persona_juridica = relationship(
        "PersonaJuridica",
        back_populates="user",
        uselist=False,
        foreign_keys="PersonaJuridica.user_id",
    )  # 1:1
    asociacion = relationship(
        "Asociacion",
        back_populates="user",
        uselist=False,
        foreign_keys="Asociacion.user_id",
    )  # 1:1
    obras_audiovisuales = relationship(
        "ObraAudiovisual",
        back_populates="user",
        foreign_keys="ObraAudiovisual.user_id",
    )  # 1:N

    # Relaciones con ESA y Exhibiciones
    estudiante_esa = relationship(
        "EstudianteESA",
        back_populates="user",
        uselist=False,
        foreign_keys="EstudianteESA.user_id",
    )  # 1:1
    salas = relationship("Sala", back_populates="user")  # 1:N
    exhibiciones = relationship("Exhibicion", back_populates="user")  # 1:N
    festivales = relationship("Festival", back_populates="user")  # 1:N

    # Comisión de Filmaciones
    rodajes = relationship("Rodaje", back_populates="user")  # 1:N

    # Fomento
    tramites_fomento = relationship("TramiteFomento", back_populates="user")  # 1:N
    evaluadores = relationship("Evaluador", back_populates="user")  # 1:N
