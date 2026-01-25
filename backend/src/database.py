from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from src.config import (
    DATABASE_URL, 
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, 
    DB_POOL_RECYCLE, DB_CONNECT_TIMEOUT, DB_STATEMENT_TIMEOUT
)

# Configuración del engine con timeouts y pool de conexiones (valores desde .env)
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": DB_CONNECT_TIMEOUT,
        "options": f"-c statement_timeout={DB_STATEMENT_TIMEOUT}"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Crear tablas en la base de datos
def init_db():
    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)

# Dependencia para obtener sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()