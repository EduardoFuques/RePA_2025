"""
Configuración centralizada del backend.

Carga las variables de entorno desde el .env en la raíz del proyecto.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Buscar el .env en la raíz del proyecto (2 niveles arriba de src/)
# Estructura: RePA_2025/.env -> backend/src/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Cargar .env si existe, sino buscar en ubicaciones alternativas
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Fallback: buscar en backend/src/.env (legacy) o backend/.env
    legacy_env = Path(__file__).resolve().parent / ".env"
    backend_env = Path(__file__).resolve().parent.parent / ".env"

    if legacy_env.exists():
        load_dotenv(legacy_env)
    elif backend_env.exists():
        load_dotenv(backend_env)
    else:
        # Último recurso: load_dotenv sin argumentos busca en cwd
        load_dotenv()

# =============================================================================
# Variables de entorno
# =============================================================================

# Entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"
IS_TESTING = (
    os.getenv("CI", "false").lower() == "true"
    or os.getenv("TESTING", "false").lower() == "true"
)

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT / Autenticación
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"  # Fijo para mayor seguridad

_DEFAULT_SECRET = "your-secret-key-change-in-production"
if IS_PRODUCTION and (not SECRET_KEY or SECRET_KEY == _DEFAULT_SECRET):
    raise RuntimeError(
        "SECRET_KEY no configurada o usa el valor por defecto. "
        'Generar una clave segura con: python -c "import secrets; print(secrets.token_hex(32))"'
    )
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE", "30"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE", "10080"))

# CORS
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
)
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Logging
LOGS_PATH = os.getenv("LOGS_PATH", "./logs")
BETTER_STACKTRACE = os.getenv("BETTER_STACKTRACE", "false").lower() == "true"

# URLs
URL_SITE = os.getenv("URL_SITE", "http://localhost:8000")

# API Root Path (para proxy reverso como nginx)
# En producción con nginx: "/api", en desarrollo local: ""
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "")

# =============================================================================
# Pool de conexiones de base de datos
# =============================================================================
# Para ~300 usuarios concurrentes: pool_size=20 + max_overflow=30 = 50 conexiones máx
# PostgreSQL default max_connections=100, así que 50 deja margen para admin/backups
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
DB_STATEMENT_TIMEOUT = int(
    os.getenv("DB_STATEMENT_TIMEOUT", "30000")
)  # en milisegundos
