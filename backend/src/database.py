from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from src.config import DATABASE_URL

# Configuración del engine con timeouts y pool de conexiones
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,              # Conexiones permanentes en el pool
    max_overflow=10,          # Conexiones adicionales permitidas
    pool_timeout=30,          # Segundos de espera para obtener conexión del pool
    pool_recycle=1800,        # Reciclar conexiones cada 30 minutos (evita stale connections)
    pool_pre_ping=True,       # Verificar conexión antes de usarla
    connect_args={
        "connect_timeout": 10,    # Timeout de conexión inicial (segundos)
        "options": "-c statement_timeout=30000"  # Timeout de queries (30 seg en ms)
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