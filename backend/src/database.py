import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
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


# Parámetros del retry de conexión.
#
# Antes viajaban como argumentos por defecto de `get_db`. Como `get_db` se usa
# vía `Depends(get_db)`, FastAPI inspeccionaba su firma y publicaba
# `max_retries` y `delay` como QUERY PARAMS en los ~180 endpoints del sistema
# (verificable en el openapi.json: `POST /users/register` los listaba entre sus
# parámetros). Son detalles de la capa de conexión, no parte del contrato de la
# API: van como constantes de módulo.
DB_RETRY_MAX = 3
DB_RETRY_DELAY = 0.5


def _conectar_con_retry() -> Session:
    """
    Abre una sesión y verifica que la conexión responda, reintentando ante
    errores transitorios con backoff exponencial.

    El retry cubre SOLO el establecimiento de la conexión. Antes envolvía
    también al `yield`, así que un error transitorio ocurrido DENTRO del
    handler volvía al loop y hacía un segundo `yield`: eso no reintenta nada
    —el request ya falló— y rompe el context manager de FastAPI con un
    RuntimeError en lugar de propagar el error original.
    """
    demora = DB_RETRY_DELAY

    for intento in range(DB_RETRY_MAX + 1):
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return db
        except (OperationalError, InterfaceError) as e:
            db.close()
            if intento < DB_RETRY_MAX:
                if not IS_TESTING:
                    logger.warning(
                        f"DB connection retry {intento + 1}/{DB_RETRY_MAX}: {str(e)}"
                    )
                time.sleep(demora)
                demora *= 2  # Backoff exponencial
            else:
                if not IS_TESTING:
                    logger.error(
                        f"DB connection failed after {DB_RETRY_MAX} retries: {str(e)}"
                    )
                raise


# Dependencia para obtener sesión con retry logic
def get_db():
    """
    Genera una sesión de base de datos, con retry automático en la conexión.

    Sin parámetros a propósito: ver DB_RETRY_MAX / DB_RETRY_DELAY arriba.
    """
    db = _conectar_con_retry()
    try:
        yield db
    finally:
        db.close()
