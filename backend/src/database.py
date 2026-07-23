import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from src.config import (
    DATABASE_URL,
    DB_CONNECT_TIMEOUT,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
    DB_STATEMENT_TIMEOUT,
    IS_TESTING,
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
        "options": f"-c statement_timeout={DB_STATEMENT_TIMEOUT}",
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Raíz del paquete backend (donde viven alembic.ini y alembic/)
BACKEND_ROOT = Path(__file__).resolve().parent.parent


def run_migrations():
    """
    Aplica las migraciones Alembic hasta `head`.

    Alembic es la **única fuente de verdad** del esquema en dev/producción.
    Se invoca de forma programática en el arranque (lifespan).
    """
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    # Evitar que env.py reconfigure el logging de la aplicación
    cfg.attributes["configure_logger"] = False
    logger.info("Aplicando migraciones Alembic (upgrade head)...")
    command.upgrade(cfg, "head")
    logger.info("Migraciones aplicadas correctamente")


def create_all_tables():
    """
    Crea todas las tablas vía metadata de los modelos.

    Reservado para el entorno de **tests** (rápido y aislado). En dev/prod el
    esquema se gestiona exclusivamente con Alembic (`run_migrations`).
    """
    import src.models  # noqa: F401  (registry completo de modelos)

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
                    logger.error(
                        f"DB connection failed after {max_retries} retries: {str(e)}"
                    )
                raise last_exception
