import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

# Modelo para Token de Verificación de Correo
class TokenRecovery(Base):
    __tablename__="token_recovery"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    token_payload = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
# Modelo asociativa para la relación muchos a muchos entre usuarios y roles
class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))

# Modelo de Role
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    rol = Column(String, unique=True, index=True, nullable=False)
    # Relación inversa definida en User

# Modelo de User
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=None, nullable=True)
    # Relación con roles a través de la tabla UserRole
    roles = relationship("Role", secondary="user_roles", backref="users")
    trainings = relationship("Training", back_populates="user")  # Relación 1:N con Training
    trabajos = relationship('Work', back_populates='user') # Relación 1:N con Trabajo
    
    # Relaciones con formularios RePA
    persona_fisica = relationship("PersonaFisica", back_populates="user", uselist=False)  # 1:1
    persona_juridica = relationship("PersonaJuridica", back_populates="user", uselist=False)  # 1:1
    asociacion = relationship("Asociacion", back_populates="user", uselist=False)  # 1:1
    obras_audiovisuales = relationship("ObraAudiovisual", back_populates="user")  # 1:N