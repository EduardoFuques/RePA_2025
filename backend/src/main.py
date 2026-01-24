from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from src.logger import logger
from src.middlewarelogg import log_requests
from starlette.middleware.base import BaseHTTPMiddleware

from src.database import init_db

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
    version="0.5.3",
    lifespan=lifespan
)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
