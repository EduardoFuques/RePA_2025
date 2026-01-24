# Changelog - Backend RePA 2025

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.6.0] - 2026-01-24

### Added
- **Health check endpoints**:
  - `/health` - Estado general con versión y conexión a BD
  - `/health/live` - Liveness probe
  - `/health/ready` - Readiness probe
- **Logging estructurado JSON** en archivos de log
  - Formato JSON con timestamp, level, module, function, line
  - Consola mantiene formato legible
  - Configurable via `LOG_LEVEL` env var

### Removed
- Módulos `training` y `work` no utilizados (873 líneas eliminadas)
  - `training_routes.py`, `admin_training_routes.py`, `work_routes.py`
  - `trainig_schemas.py`, `work_schemas.py`
  - `training_models.py`, `work_models.py`

---

## [0.5.3] - 2026-01-24

### Added
- **Alembic para migraciones de base de datos**:
  - Configuración inicial con `alembic init`
  - `env.py` configurado para usar `DATABASE_URL` desde variables de entorno
  - Migración inicial `bc2bcbe0847e_initial_migration.py`
  - Soporte para autogenerate de migraciones
- Archivo `.env.example` con configuración de ejemplo
- Puerto 5432 expuesto en `docker-compose.yml` para desarrollo local

---

## [0.5.2] - 2026-01-24

### Changed
- **Migrado `on_event` a `lifespan` handler** (FastAPI moderno)
- **Corregidos deprecation warnings de Pydantic v2**:
  - `class Config` → `model_config = ConfigDict(from_attributes=True)`
  - `@validator` → `@field_validator` con `@classmethod`
  - Afecta 10 archivos de schemas

### Fixed
- Warnings reducidos de 49 a 24 en tests

---

## [0.5.1] - 2026-01-24

### Changed
- **Tests migrados a PostgreSQL real** usando testcontainers
  - Reemplazado SQLite en memoria por PostgresContainer
  - 33/33 tests pasando (100%)
- **Versiones de dependencias fijadas** en `requirements.txt`
  - Rangos de versiones compatibles para evitar breaking changes

### Fixed
- Renombrado `admin_training_rutes.py` → `admin_training_routes.py` (typo)
- Tests de autenticación que estaban en skip ahora funcionan

---

## [0.5.0] - 2026-01-24

### Added
- **Modelo EstudianteESA** (`esa_model.py`) - Registro de estudiantes del audiovisual:
  - Datos personales, localización, formación, intereses, declaraciones
  - Vigencia de 1 año con renovación automática
- **Modelos de Exhibiciones** (`exhibicion_model.py`):
  - `Sala` - Salas de exhibición con características técnicas
  - `Exhibicion` - Registro de proyecciones con espectadores y recaudación
  - `Festival` - Festivales de cine con categorías y apoyo IAAviM
  - `Cinemateca` - Gestión del archivo físico de obras
- **Schemas Pydantic** para ESA y Exhibiciones
- **Rutas CRUD** para ESA (`/esa`) y Exhibiciones (`/exhibiciones`)
- **Suite de Tests** con pytest:
  - `conftest.py` - Configuración y fixtures
  - `test_auth.py` - Tests de autenticación
  - `test_persona_fisica.py` - Tests de Persona Física
  - `test_esa.py` - Tests de Estudiantes ESA
  - `test_exhibiciones.py` - Tests de Salas, Exhibiciones, Festivales
- Dependencias de testing: pytest, pytest-asyncio, httpx

### Changed
- Versión de la API actualizada a 0.5.0
- Relaciones agregadas en User y ObraAudiovisual

---

## [0.4.0] - 2026-01-23

### Added
- **Schemas Pydantic** para validación de datos:
  - `persona_fisica_schemas.py` - Create, Update, Out para PF y subperfiles
  - `persona_juridica_schemas.py` - Create, Update, Out para PJ e integrantes
  - `asociacion_schemas.py` - Create, Update, Out para AS e integrantes
  - `obra_audiovisual_schemas.py` - Create, Update, Out para AGAM y equipo técnico
- **Rutas CRUD** para formularios RePA:
  - `/persona-fisica` - CRUD completo + endpoints para cada subperfil
  - `/persona-juridica` - CRUD completo + gestión de integrantes
  - `/asociacion` - CRUD completo + gestión de integrantes
  - `/obras` - CRUD completo + gestión de equipo técnico
- Rutas registradas en `main.py` con tags para documentación Swagger

### Changed
- Versión de la API actualizada a 0.4.0

---

## [0.3.0] - 2026-01-23

### Added
- **Modelo PersonaFisica** (`persona_fisica_model.py`) - Reemplaza Person con estructura completa:
  - Datos personales, educación, identidades, situación laboral, interés institucional
  - Subperfiles: Productor, Director, Guionista, Documentalista, Realizador Integral, Técnico/Artístico, Capacitador, Investigador
- **Modelo PersonaJuridica** (`persona_juridica_model.py`):
  - Datos institucionales, domicilio, representación legal, actividades, documentación
  - Tabla de integrantes vinculados
- **Modelo Asociacion** (`asociacion_model.py`):
  - Datos básicos, representación, ámbitos de actuación, documentación
  - Tabla de integrantes vinculados
- **Modelo ObraAudiovisual** (`obra_audiovisual_model.py`) para AGAM:
  - Identificación, datos técnicos, datos relacionales, derechos
  - Tabla de equipo técnico
- Archivo `models/__init__.py` para registro centralizado de modelos
- Relaciones en User: persona_fisica, persona_juridica, asociacion, obras_audiovisuales

### Removed
- Archivo `person_model.py` (reemplazado por `persona_fisica_model.py`)

---

## [0.2.0] - 2026-01-23

### Added
- Archivo `CHANGELOG.md` para tracking de cambios
- Archivo `BACKEND_ANALISIS.md` con análisis completo del estado del backend
- Variable de entorno `CORS_ORIGINS` para configurar orígenes permitidos

### Fixed
- Corregido import en `person_model.py` (`src.db.database` → `src.database`)
- Corregido FK de Person (`user_email` → `user_id`) para relación correcta con usuarios
- Corregido bug `db` no definida en `/users/me` GET - agregada dependency `db: Session = Depends(get_db)`
- Corregido filtro en `/users/me` GET (`current_user["sub"]` → `current_user["id"]`)
- Corregido bug en `training_routes.py` línea 119 (`training` → `trainings`)

### Changed
- Versión de la API actualizada a 0.2.0
- CORS ahora se configura desde variable de entorno en lugar de wildcard `*`
- Prints de debug reemplazados por `logger.debug()` en `utils.py`
- Removidos prints de debug en `user_routes.py` y `seed.py`

### Security
- CORS configurado por entorno (default: localhost:3000, localhost:5173, localhost:80)
- Removida exposición de información sensible en logs de producción

---

## [0.1.0] - 2025-XX-XX (Versión inicial)

### Added
- Sistema de autenticación JWT con access y refresh tokens
- CRUD de usuarios con verificación de email
- Sistema de roles (admin/user) con permisos
- Módulo de capacitaciones (Training) con CRUD completo
- Módulo de trabajos (Work) con roles y tareas
- Modelo base de Person (incompleto)
- Configuración Docker con PostgreSQL y Adminer
- Middleware de logging
- Seed de datos iniciales (roles)

### Known Issues
- Modelo Person tiene import incorrecto
- Modelo Person usa `user_email` en lugar de `user_id`
- Endpoint `/users/me` GET no tiene dependency `db`
- Bug de referencia en `training_routes.py` línea 119
- CORS abierto a todos los orígenes
- Prints de debug en código de producción

---

*Última actualización: 23/01/2026*
