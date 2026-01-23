from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from src.logger import logger
from src.middlewarelogg import log_requests
from starlette.middleware.base import BaseHTTPMiddleware # Importar BaseHTTPMiddleware para el middleware de logs

from src.database import init_db

from src.routes.user_routes import user_router
from src.routes.admin_routes import admin_router
from src.routes.training_routes import training_router
from src.routes.admin_training_rutes import admin_training
from src.routes.work_routes import work_router

from src.seed import seed_data

load_dotenv()

# Inicializar la base de datos
init_db()

app = FastAPI()
app.title = "Backend RePA - 2025"
app.version = "0.2.0"
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

logger.info("FastAPI iniciado correctamente...")

# CORS - Cargar orígenes desde variable de entorno
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in cors_origins_str.split(",")]

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos y ejecutar seeding
@app.on_event("startup")
def on_startup():
    init_db()  # Crear tablas si no existen
    seed_data()  # Ejecutar seeding

# Incluir rutas a módulos
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(training_router, prefix="/training", tags=["Training"])
app.include_router(work_router, prefix="/work", tags=["Work"])

# Rutas de Administración
app.include_router(admin_router, prefix="/admin_user", tags=["Administrator User"])
app.include_router(admin_training, prefix="/admin_training", tags=["Administrator Training"])

@app.get("/")
def root():
    logger.info("ROOT - FastAPI funcionando correctamente...")
    return {"message": "FastAPI funcionando correctamente..."}
