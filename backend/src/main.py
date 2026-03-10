from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import API_ROOT_PATH, CORS_ORIGINS, IS_PRODUCTION
from src.database import get_db, init_db
from src.logger import logger
from src.middlewarelogg import log_requests
from src.rate_limiter import limiter, rate_limit_exceeded_handler
from src.routes.admin_routes import admin_router
from src.routes.asociacion_routes import asociacion_router
from src.routes.esa_routes import esa_router
from src.routes.exhibicion_routes import exhibicion_router
from src.routes.fomento_routes import fomento_router
from src.routes.obra_audiovisual_routes import obra_audiovisual_router
from src.routes.persona_fisica_routes import persona_fisica_router
from src.routes.persona_juridica_routes import persona_juridica_router
from src.routes.rodaje_routes import rodaje_router
from src.routes.upload_routes import files_router, upload_router
from src.routes.user_routes import user_router
from src.seed import seed_data


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


app = FastAPI(
    title="API RePA - Registro Provincial del Audiovisual",
    root_path=API_ROOT_PATH,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
    description="""
## Sistema de Registro del Sector Audiovisual de Misiones

La API de RePA permite gestionar el registro de:

- **Personas Físicas**: Realizadores, técnicos, productores del sector audiovisual
- **Personas Jurídicas**: Productoras, cooperativas, empresas audiovisuales
- **Asociaciones/Colectivos**: Grupos y colectivos audiovisuales
- **Estudiantes ESA**: Estudiantes del sector audiovisual (registro temporal)
- **Exhibiciones**: Salas, festivales, cinematecas
- **Obras Audiovisuales (AGAM)**: Registro de obras audiovisuales

### Autenticación

La API utiliza **JWT (JSON Web Tokens)** para autenticación.
Para acceder a endpoints protegidos, incluir el header:

```
Authorization: Bearer <token>
```

### Rate Limiting

Los endpoints sensibles tienen límites de solicitudes:
- **Login**: 5 intentos por minuto
- **Registro**: 10 solicitudes por minuto
- **Recuperación de contraseña**: 3 solicitudes por minuto

### Contacto

- **IAAviM** - Instituto de Artes Audiovisuales de Misiones
- **Email**: sistemas@iaavim.gob.ar
    """,
    version="1.5.9",
    contact={
        "name": "IAAviM - Sistemas",
        "url": "https://iaavim.gob.ar",
        "email": "sistemas@iaavim.gob.ar",
    },
    license_info={
        "name": "Uso interno - Gobierno de Misiones",
    },
    openapi_tags=[
        {
            "name": "Users",
            "description": "Registro, autenticación y gestión de usuarios",
        },
        {
            "name": "Persona Física",
            "description": "Formulario de registro para personas físicas del sector audiovisual",
        },
        {
            "name": "Persona Jurídica",
            "description": "Formulario de registro para empresas y productoras audiovisuales",
        },
        {
            "name": "Asociación/Colectivo",
            "description": "Formulario de registro para asociaciones y colectivos audiovisuales",
        },
        {
            "name": "Estudiantes ESA",
            "description": "Registro temporal para estudiantes del sector audiovisual (vigencia 1 año)",
        },
        {
            "name": "Obras Audiovisuales (AGAM)",
            "description": "Registro de obras audiovisuales producidas en Misiones",
        },
        {
            "name": "Exhibiciones, Salas, Festivales, Cinemateca",
            "description": "Registro de espacios de exhibición audiovisual",
        },
        {
            "name": "Comisión de Filmaciones",
            "description": "Archivo de rodajes, permisos y cartas de aval institucional",
        },
        {
            "name": "Administrator User",
            "description": "Endpoints de administración (requiere rol admin)",
        },
        {"name": "Health", "description": "Endpoints de monitoreo y health checks"},
    ],
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Configuración de CORS - Restringido a métodos y headers necesarios
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Middleware de logging (se ejecuta después de CORS)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

# Incluir rutas a módulos
app.include_router(user_router, prefix="/users", tags=["Users"])

# Rutas de formularios RePA
app.include_router(
    persona_fisica_router, prefix="/persona-fisica", tags=["Persona Física"]
)
app.include_router(
    persona_juridica_router, prefix="/persona-juridica", tags=["Persona Jurídica"]
)
app.include_router(
    asociacion_router, prefix="/asociacion", tags=["Asociación/Colectivo"]
)
app.include_router(
    obra_audiovisual_router, prefix="/obras", tags=["Obras Audiovisuales (AGAM)"]
)
app.include_router(esa_router, prefix="/esa", tags=["Estudiantes ESA"])
app.include_router(
    exhibicion_router,
    prefix="/exhibiciones",
    tags=["Exhibiciones, Salas, Festivales, Cinemateca"],
)
app.include_router(rodaje_router, prefix="/rodajes", tags=["Comisión de Filmaciones"])
app.include_router(fomento_router, tags=["Fomento"])

# Rutas de Administración
app.include_router(admin_router, prefix="/admin_user", tags=["Administrator User"])

# Rutas de Upload de archivos
app.include_router(upload_router, tags=["Upload"])
app.include_router(files_router, tags=["Files"])


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
        "database": db_status,
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
