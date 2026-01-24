# Backend RePA 2025 - Análisis v0.5.3

## Resumen

Backend API REST con **FastAPI + PostgreSQL + SQLAlchemy**. Autenticación JWT con roles.

**Estado:** ✅ 100% operativo | 33/33 tests pasando | Migraciones con Alembic

---

## 1. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | >=0.115.0 |
| ORM | SQLAlchemy | >=2.0.0 |
| Base de datos | PostgreSQL | 15+ |
| Migraciones | Alembic | >=1.13.0 |
| Autenticación | JWT (python-jose) | >=3.3.0 |
| Validación | Pydantic | >=2.0.0 |
| Testing | pytest + testcontainers | >=8.0.0 |

---

## 2. Estructura del Proyecto

```
backend/
├── alembic/                 # Migraciones de BD
│   ├── env.py
│   └── versions/
├── tests/                   # Suite de tests (33 tests)
│   ├── conftest.py          # Fixtures con testcontainers
│   ├── test_auth.py
│   ├── test_persona_fisica.py
│   ├── test_esa.py
│   └── test_exhibiciones.py
├── src/
│   ├── main.py              # FastAPI app (lifespan handler)
│   ├── database.py          # SQLAlchemy config
│   ├── models/              # 9 archivos de modelos
│   ├── schemas/             # 10 archivos de schemas
│   └── routes/              # 12 archivos de rutas
├── alembic.ini
├── .env.example
├── Dockerfile
└── requirements.txt
```

---

## 3. Modelos Implementados

| Modelo | Archivo | Tablas |
|--------|---------|--------|
| Users | `user_models.py` | `users`, `roles`, `user_roles` |
| PersonaFisica | `persona_fisica_model.py` | `personas_fisicas` + 8 subperfiles |
| PersonaJuridica | `persona_juridica_model.py` | `personas_juridicas`, `integrantes_pj` |
| Asociacion | `asociacion_model.py` | `asociaciones`, `integrantes_asociacion` |
| ObraAudiovisual | `obra_audiovisual_model.py` | `obras_audiovisuales`, `equipo_tecnico` |
| EstudianteESA | `esa_model.py` | `estudiantes_esa` |
| Exhibiciones | `exhibicion_model.py` | `salas`, `exhibiciones`, `festivales`, `cinemateca` |
| Training | `training_models.py` | `trainings` |
| Work | `work_models.py` | `trabajos`, `roles`, `tareas` |

---

## 4. Endpoints API

| Prefijo | Descripción | Endpoints |
|---------|-------------|-----------|
| `/users` | Autenticación y perfil | 8 |
| `/admin_user` | Administración usuarios | 5 |
| `/persona-fisica` | Formulario PF | 20+ |
| `/persona-juridica` | Formulario PJ | 8 |
| `/asociacion` | Formulario AS | 8 |
| `/obras` | AGAM | 10 |
| `/esa` | Estudiantes ESA | 6 |
| `/exhibiciones` | Salas, Exhibiciones, Festivales, Cinemateca | 16 |
| `/training` | Capacitaciones | 5 |
| `/work` | Trabajos | 7 |

**Documentación:** Swagger UI en `/docs`

---

## 5. Tests

```
33 passed, 24 warnings in ~29s
```

| Archivo | Tests |
|---------|-------|
| `test_auth.py` | 9 |
| `test_persona_fisica.py` | 9 |
| `test_esa.py` | 6 |
| `test_exhibiciones.py` | 9 |

**Configuración:** PostgreSQL real con `testcontainers` (no SQLite)

---

## 6. Comandos Útiles

```bash
# Docker
docker-compose up -d
docker logs repa_2025-backend-1

# Tests (local con Docker Desktop corriendo)
cd backend
pytest tests/ -v

# Alembic
alembic current
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

---

## 7. Historial de Versiones

| Versión | Cambios Principales |
|---------|---------------------|
| v0.2.0 | Corrección bugs críticos, CORS, logging |
| v0.3.0 | Modelos PF, PJ, AS, AGAM |
| v0.4.0 | Schemas y rutas CRUD |
| v0.5.0 | Modelos ESA, Exhibiciones, Tests |
| v0.5.1 | Tests con PostgreSQL, dependencias fijadas |
| v0.5.2 | Deprecation warnings Pydantic/FastAPI |
| v0.5.3 | Alembic migraciones |

---

## 8. Tareas Pendientes

| Prioridad | Tarea |
|-----------|-------|
| 🟢 Baja | Implementar health checks |
| 🟢 Baja | Configurar logging estructurado |
| 🟢 Baja | Corregir typo `trainig_schemas.py` |

---

*Última actualización: 24/01/2026 - v0.5.3*
