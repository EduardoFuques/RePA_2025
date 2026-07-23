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

# Entorno — fail-closed: sin ENVIRONMENT explícito el backend no arranca.
# Un ENVIRONMENT ausente o con typo activaba silenciosamente el modo development
# (seed de usuarios de prueba con credenciales conocidas, rate limiter off,
# /docs expuesto, SECRET_KEY default aceptada). Ahora solo se aceptan valores
# conocidos; los tests (TESTING/CI) caen a "testing" automáticamente.
IS_TESTING = (
    os.getenv("CI", "false").lower() == "true"
    or os.getenv("TESTING", "false").lower() == "true"
)

_VALID_ENVIRONMENTS = ("development", "production", "testing")
_env_raw = os.getenv("ENVIRONMENT")
if _env_raw is None and IS_TESTING:
    _env_raw = "testing"
if _env_raw is None:
    raise RuntimeError(
        "ENVIRONMENT no está definida. Definir explícitamente "
        f"ENVIRONMENT={'|'.join(_VALID_ENVIRONMENTS)} en el entorno o .env. "
        "El backend no asume 'development' por defecto para evitar desplegar "
        "producción con configuración de desarrollo."
    )
ENVIRONMENT = _env_raw.strip().lower()
if ENVIRONMENT not in _VALID_ENVIRONMENTS:
    raise RuntimeError(
        f"ENVIRONMENT='{_env_raw}' no es un valor válido. "
        f"Valores permitidos: {', '.join(_VALID_ENVIRONMENTS)}."
    )
IS_PRODUCTION = ENVIRONMENT == "production"

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

# URL pública del FRONTEND — para armar los links de confirmación de cuenta y
# recuperación de contraseña que van en los emails (a diferencia de URL_SITE,
# que apunta a la API y no tiene pantallas para consumir esos tokens).
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# =============================================================================
# Email transaccional (verificación de cuenta, recuperación de contraseña)
# =============================================================================
# Sin SMTP_HOST configurado no se envían emails reales — en desarrollo/testing
# el token ya se devuelve directamente en la respuesta de la API para pruebas
# manuales (ver IS_PRODUCTION en user_routes.py), así que esto no bloquea el
# flujo local. En producción SÍ hace falta: sin esto, un usuario nuevo no
# tiene forma de activar su cuenta ni de recuperar su contraseña.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-responder@iaavim.gob.ar")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
# SSL implícito (puerto 465, ej. Mailosaur) en vez de STARTTLS (puerto 587).
# Mutuamente excluyente con SMTP_USE_TLS en la práctica; default false para
# no cambiar el comportamiento de nadie que no lo configure explícitamente.
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

if IS_PRODUCTION and not SMTP_HOST:
    import sys

    print(
        "[WARN] SMTP_HOST no está configurado en producción: los emails de "
        "verificación de cuenta y recuperación de contraseña no se van a "
        "enviar. Los usuarios nuevos no van a poder activar su cuenta.",
        file=sys.stderr,
    )

# =============================================================================
# Gating del Padrón RePA
# =============================================================================
# Cuando está activo, los formularios PJ/AS/AGAM/Sala/Festival/Exhibición exigen
# que el usuario tenga su Persona Física (PF) APROBADA antes de poder crearlos.
# Por defecto OFF: se activará junto con el onboarding del frontend (Fase 4 del
# plan de implementación del Código RePA) para no romper la app en producción.
REPA_GATING_ENABLED = os.getenv("REPA_GATING_ENABLED", "false").lower() == "true"

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
