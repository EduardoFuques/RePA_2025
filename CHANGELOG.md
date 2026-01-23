# Changelog - Backend RePA 2025

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
