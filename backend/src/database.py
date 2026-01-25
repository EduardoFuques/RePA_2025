import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, InterfaceError

from src.config import (
    DATABASE_URL, 
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, 
    DB_POOL_RECYCLE, DB_CONNECT_TIMEOUT, DB_STATEMENT_TIMEOUT,
    IS_TESTING
)
from src.logger import logger

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

# Dependencia para obtener sesión con retry logic
def get_db(max_retries: int = 3, delay: float = 0.5):
    """
    Genera una sesión de base de datos con retry automático.
    
    Si la conexión falla por errores transitorios (conexión perdida, timeout),
    reintenta hasta max_retries veces con backoff exponencial.
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_retries + 1):
        try:
            db = SessionLocal()
            # Verificar que la conexión funciona
            db.execute(text("SELECT 1"))
            try:
                yield db
            finally:
                db.close()
            return
        except (OperationalError, InterfaceError) as e:
            last_exception = e
            if attempt < max_retries:
                if not IS_TESTING:
                    logger.warning(
                        f"DB connection retry {attempt + 1}/{max_retries}: {str(e)}"
                    )
                time.sleep(current_delay)
                current_delay *= 2  # Backoff exponencial
            else:
                if not IS_TESTING:
                    logger.error(f"DB connection failed after {max_retries} retries: {str(e)}")
                raise last_exception