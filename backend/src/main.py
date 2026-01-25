from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from src.logger import logger
from src.database import get_db, init_db
from src.middlewarelogg import log_requests
from src.rate_limiter import limiter, rate_limit_exceeded_handler
from starlette.middleware.base import BaseHTTPMiddleware

from src.routes.user_routes import user_router
from src.routes.admin_routes import admin_router
from src.routes.persona_fisica_routes import persona_fisica_router
from src.routes.persona_juridica_routes import persona_juridica_router
from src.routes.asociacion_routes import asociacion_router
from src.routes.obra_audiovisual_routes import obra_audiovisual_router
from src.routes.esa_routes import esa_router
from src.routes.exhibicion_routes import exhibicion_router

from src.seed import seed_data

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para startup y shutdown"""
    # Startup
    init_db()
    seed_data()
    logger.info("FastAPI iniciado correctamente...")
    yield
    # Shutdown (si necesitas limpiar recursos, va aquí)
    logger.info("FastAPI cerrando...")


# CORS - Cargar orígenes desde variable de entorno
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in cors_origins_str.split(",")]

app = FastAPI(
    title="Backend RePA - 2025",
    version="0.7.0",
    lifespan=lifespan
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Configuración de CORS - Restringido a métodos y headers necesarios
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Middleware de logging (se ejecuta después de CORS)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

# Incluir rutas a módulos
app.include_router(user_router, prefix="/users", tags=["Users"])

# Rutas de formularios RePA
app.include_router(persona_fisica_router, prefix="/persona-fisica", tags=["Persona Física"])
app.include_router(persona_juridica_router, prefix="/persona-juridica", tags=["Persona Jurídica"])
app.include_router(asociacion_router, prefix="/asociacion", tags=["Asociación/Colectivo"])
app.include_router(obra_audiovisual_router, prefix="/obras", tags=["Obras Audiovisuales (AGAM)"])
app.include_router(esa_router, prefix="/esa", tags=["Estudiantes ESA"])
app.include_router(exhibicion_router, prefix="/exhibiciones", tags=["Exhibiciones, Salas, Festivales, Cinemateca"])

# Rutas de Administración
app.include_router(admin_router, prefix="/admin_user", tags=["Administrator User"])

@app.get("/")
def root():
    logger.info("ROOT - FastAPI funcionando correctamente...")
    return {"message": "FastAPI funcionando correctamente..."}


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint para verificar el estado del servicio.
    Verifica conexión a la base de datos.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check - DB error: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": app.version,
        "database": db_status
    }


@app.get("/health/live", tags=["Health"])
def liveness():
    """Liveness probe - verifica que la aplicación está corriendo."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
def readiness(db: Session = Depends(get_db)):
    """Readiness probe - verifica que la aplicación puede recibir tráfico."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}
