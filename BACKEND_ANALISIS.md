# Análisis del Backend RePA 2025

## Resumen Ejecutivo

El backend de RePA 2025 es una API REST desarrollada en **FastAPI** con **PostgreSQL** como base de datos, utilizando **SQLAlchemy** como ORM. Implementa autenticación JWT con sistema de roles y permisos.

**Estado actual (v0.5.3):** Backend **100% operativo** con todos los módulos implementados:
- ✅ Autenticación y usuarios
- ✅ Formularios RePA completos (PF, PJ, AS, AGAM)
- ✅ Módulos IAAViM (ESA, Cinemateca, Exhibiciones, Salas, Festivales)
- ✅ Suite de tests con PostgreSQL real (33/33 pasando)
- ✅ Migraciones con Alembic

---

## 1. Arquitectura y Estructura

### 1.1 Stack Tecnológico
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | >=0.115.0 |
| ORM | SQLAlchemy | >=2.0.0 |
| Base de datos | PostgreSQL | 15+ |
| Migraciones | Alembic | >=1.13.0 |
| Autenticación | JWT (python-jose) | >=3.3.0 |
| Hashing | bcrypt/passlib | >=4.0.0 |
| Validación | Pydantic | >=2.0.0 |
| Testing | pytest + testcontainers | >=8.0.0 |
| Contenedores | Docker Compose | 3 |

### 1.2 Estructura de Directorios (v0.5.3)
```
backend/
├── alembic/                 # Migraciones de BD
│   ├── env.py
│   ├── versions/
│   └── script.py.mako
├── alembic.ini              # Configuración Alembic
├── tests/                   # Suite de tests
│   ├── conftest.py          # Fixtures (testcontainers)
│   ├── test_auth.py
│   ├── test_persona_fisica.py
│   ├── test_esa.py
│   └── test_exhibiciones.py
├── src/
│   ├── main.py              # Punto de entrada FastAPI (lifespan)
│   ├── database.py          # Configuración SQLAlchemy
│   ├── seed.py              # Datos iniciales (roles)
│   ├── utils.py             # Utilidades (auth, validaciones)
│   ├── token_utils.py       # Manejo de JWT
│   ├── logger.py            # Configuración de logs
│   ├── middlewarelogg.py    # Middleware de logging
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_models.py
│   │   ├── persona_fisica_model.py
│   │   ├── persona_juridica_model.py
│   │   ├── asociacion_model.py
│   │   ├── obra_audiovisual_model.py
│   │   ├── esa_model.py
│   │   ├── exhibicion_model.py
│   │   ├── training_models.py
│   │   └── work_models.py
│   ├── schemas/
│   │   ├── user_schemas.py
│   │   ├── persona_fisica_schemas.py
│   │   ├── persona_juridica_schemas.py
│   │   ├── asociacion_schemas.py
│   │   ├── obra_audiovisual_schemas.py
│   │   ├── esa_schemas.py
│   │   ├── exhibicion_schemas.py
│   │   ├── trainig_schemas.py
│   │   └── work_schemas.py
│   └── routes/
│       ├── user_routes.py
│       ├── admin_routes.py
│       ├── persona_fisica_routes.py
│       ├── persona_juridica_routes.py
│       ├── asociacion_routes.py
│       ├── obra_audiovisual_routes.py
│       ├── esa_routes.py
│       ├── exhibicion_routes.py
│       ├── training_routes.py
│       ├── admin_training_routes.py
│       └── work_routes.py
├── .env.example
├── Dockerfile
└── requirements.txt
```

---

## 2. Modelos de Datos Implementados

### 2.1 Usuarios y Autenticación
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │   user_roles    │     │     roles       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (UUID) PK    │────<│ user_id FK      │>────│ id PK           │
│ email UK        │     │ role_id FK      │     │ rol UK          │
│ hashed_password │     └─────────────────┘     └─────────────────┘
│ is_active       │
│ created_at      │     ┌─────────────────┐
│ last_login      │     │ token_recovery  │
└─────────────────┘     ├─────────────────┤
                        │ id (UUID) PK    │
                        │ user_id FK      │
                        │ token_payload   │
                        │ created_at      │
                        │ expires_at      │
                        │ is_active       │
                        └─────────────────┘
```

### 2.2 Capacitaciones (Training)
```
┌─────────────────────────┐
│       trainings         │
├─────────────────────────┤
│ id PK                   │
│ user_id FK → users      │
│ nombre_curso            │
│ institucion             │
│ tipo_certificado        │
│ nivel_estudio           │
│ fecha_inicio            │
│ fecha_finalizacion      │
│ horas_duracion          │
│ enlace_certificado      │
│ area_conocimiento       │
│ descripcion_curso       │
│ calificacion_nota       │
│ idioma                  │
│ nombre_profesor         │
│ nombre_programa         │
│ pais, ciudad, estado    │
│ observaciones           │
└─────────────────────────┘
```

### 2.3 Trabajos (Works)
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    trabajos     │     │ trabajos_roles  │     │  rol_at_work    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id PK           │────<│ trabajo_id FK   │>────│ id PK           │
│ user_id FK      │     │ rol_id FK       │     │ nombre UK       │
│ titulo_prod     │     └─────────────────┘     └─────────────────┘
│ tipo_produccion │
│ fecha_inicio    │     ┌─────────────────┐     ┌─────────────────┐
│ fecha_fin       │     │ trabajos_tareas │     │ tareas_at_work  │
│ descripcion     │────<│ trabajo_id FK   │>────│ id PK           │
│ enlace_portaf   │     │ tarea_id FK     │     │ nombre UK       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 2.4 Persona (Modelo definido pero NO integrado)
```
┌─────────────────────────┐
│       persons           │
├─────────────────────────┤
│ id PK                   │
│ user_email FK → users   │  ⚠️ Error: debería ser user_id
│ nombre, apellido        │
│ dni_cuit_cuil UK        │
│ fecha_nacimiento        │
│ nacionalidad            │
│ identidad_genero        │
│ etnia, etnia_nombre     │
│ estado_civil            │
│ educacion_*             │
│ personas_a_cargo        │
│ tipo_contribuyente      │
│ actividad_registrada    │
│ telefono                │
│ dir_* (dirección)       │
└─────────────────────────┘
```

---

## 3. Endpoints API Disponibles

### 3.1 Usuarios (`/users`)
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/register` | Registrar nuevo usuario | No |
| POST | `/confirm/{token}` | Verificar email | No |
| POST | `/token` | Login (obtener JWT) | No |
| PUT | `/recovery_passwd` | Solicitar recuperación | No |
| GET | `/recovery/{token}` | Confirmar recuperación | No |
| GET | `/me` | Obtener usuario actual | Sí |
| PUT | `/me` | Actualizar usuario actual | Sí |
| DELETE | `/me` | Toggle is_active | Sí |

### 3.2 Administración (`/admin_user`)
| Método | Endpoint | Descripción | Auth | Rol |
|--------|----------|-------------|------|-----|
| GET | `/users` | Listar todos los usuarios | Sí | admin |
| GET | `/{user_id}` | Obtener usuario por ID | Sí | admin |
| PUT | `/{user_id}` | Actualizar usuario | Sí | admin |
| PUT | `/{user_id}/roles` | Modificar roles | Sí | admin |
| DELETE | `/{user_id}` | Toggle is_active | Sí | admin |

### 3.3 Capacitaciones (`/training`)
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/create` | Crear capacitación | Sí |
| PUT | `/update/{id}` | Actualizar capacitación | Sí |
| GET | `/me/{id}` | Obtener capacitación | Sí |
| GET | `/list` | Listar capacitaciones | Sí |
| DELETE | `/delete/{id}` | Eliminar capacitación | Sí |

### 3.4 Trabajos (`/work`)
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/` | Listar trabajos | Sí |
| POST | `/` | Crear trabajo | Sí |
| GET | `/{id}` | Obtener trabajo | Sí |
| PUT | `/{id}` | Actualizar trabajo | Sí |
| DELETE | `/{id}` | Eliminar trabajo | Sí |
| GET | `/roles` | Listar roles de trabajo | Sí |
| GET | `/tareas` | Listar tareas | Sí |

---

## 4. Estado de Correcciones

### 4.1 ✅ Problemas Críticos - TODOS RESUELTOS

| Problema | Versión | Solución |
|----------|---------|----------|
| CORS abierto a todos | v0.2.0 | Variable de entorno `CORS_ORIGINS` |
| Import incorrecto en person_model | v0.3.0 | Reemplazado por `persona_fisica_model.py` |
| FK incorrecta (user_email) | v0.3.0 | Nuevo modelo con `user_id` |
| Variable `db` no definida | v0.2.0 | Agregada dependency `Depends(get_db)` |
| Bug variable `training` | v0.2.0 | Corregido a `trainings` |
| Prints de debug | v0.2.0 | Reemplazados por `logger.debug()` |
| Typo `admin_training_rutes.py` | v0.5.1 | Renombrado a `admin_training_routes.py` |
| Deprecation Pydantic v2 | v0.5.2 | Migrado a `model_config = ConfigDict()` |
| Deprecation `on_event` | v0.5.2 | Migrado a `lifespan` context manager |
| Sin migraciones de BD | v0.5.3 | Implementado Alembic |
| Dependencias sin versiones | v0.5.1 | Fijadas en `requirements.txt` |

### 4.2 🟡 Pendientes Menores

| Problema | Prioridad | Descripción |
|----------|-----------|-------------|
| Typo `trainig_schemas.py` | Baja | Debería ser `training_schemas.py` |
| Validación email único en update | Baja | No verifica duplicados al actualizar |
| Hash en token de recuperación | Baja | El hash viaja en el token |
| Endpoint refresh token | Baja | Login genera token pero no hay endpoint |

---

## 5. Modelos Faltantes para Frontend

### 5.1 Comparación Frontend vs Backend (Actualizado v0.5.0)

| Formulario Frontend | Modelo Backend | Estado |
|---------------------|----------------|--------|
| **Persona Física (PF)** | PersonaFisica + 8 subperfiles | ✅ Completo |
| **Persona Jurídica (PJ)** | PersonaJuridica + IntegrantePJ | ✅ Completo |
| **Asociación/Colectivo (AS)** | Asociacion + IntegranteAsociacion | ✅ Completo |
| **AGAM (Obras)** | ObraAudiovisual + EquipoTecnicoObra | ✅ Completo |
| **ESA (Estudiantes)** | EstudianteESA | ✅ Completo (v0.5.0) |
| **Cinemateca** | Cinemateca | ✅ Completo (v0.5.0) |
| **Exhibiciones** | Exhibicion | ✅ Completo (v0.5.0) |
| **Salas de Exhibición** | Sala | ✅ Completo (v0.5.0) |
| **Festivales** | Festival | ✅ Completo (v0.5.0) |

### 5.2 Modelos Implementados (v0.5.0)

> **Nota:** Todos los modelos requeridos han sido implementados. Ver archivos en `backend/src/models/`.

#### ✅ Persona Física - `persona_fisica_model.py`
- `PersonaFisica` + 8 subperfiles (Productor, Director, Guionista, Documentalista, RealizadorIntegral, TecnicoArtistico, Capacitador, Investigador)

#### ✅ Persona Jurídica - `persona_juridica_model.py`
- `PersonaJuridica` + `IntegrantePJ`

#### ✅ Asociación/Colectivo - `asociacion_model.py`
- `Asociacion` + `IntegranteAsociacion`

#### ✅ AGAM (Obras Audiovisuales) - `obra_audiovisual_model.py`
- `ObraAudiovisual` + `EquipoTecnicoObra`

#### ✅ ESA (Estudiantes) - `esa_model.py`
- `EstudianteESA` (vigencia 1 año con renovación)

#### ✅ Exhibiciones - `exhibicion_model.py`
- `Sala` - Salas de exhibición
- `Exhibicion` - Registro de proyecciones
- `Festival` - Festivales de cine
- `Cinemateca` - Archivo físico de obras

### 5.3 Endpoints Disponibles

| Prefijo | Modelo | Métodos |
|---------|--------|---------|
| `/persona-fisica` | PersonaFisica | CRUD + subperfiles |
| `/persona-juridica` | PersonaJuridica | CRUD + integrantes |
| `/asociacion` | Asociacion | CRUD + integrantes |
| `/obras` | ObraAudiovisual | CRUD + equipo técnico |
| `/esa` | EstudianteESA | CRUD + renovación |
| `/exhibiciones` | Exhibicion | CRUD |
| `/exhibiciones/salas` | Sala | CRUD |
| `/exhibiciones/festivales` | Festival | CRUD |
| `/exhibiciones/cinemateca` | Cinemateca | CRUD |

---

## 6. Plan de Integración Frontend-Backend (Actualizado v0.5.0)

### ✅ Fase 1: Correcciones Críticas - COMPLETADA (v0.2.0)
1. ~~Corregir import en `person_model.py`~~ ✅
2. ~~Corregir FK de Person (user_email → user_id)~~ ✅
3. ~~Agregar `db` dependency en `/users/me` GET~~ ✅
4. ~~Corregir bug en `training_routes.py`~~ ✅
5. ~~Configurar CORS por entorno~~ ✅

### ✅ Fase 2: Modelos Base - COMPLETADA (v0.3.0)
1. ~~Completar modelo PersonaFisica con campos del frontend~~ ✅
2. ~~Crear modelo PersonaJuridica~~ ✅
3. ~~Crear modelo Asociacion~~ ✅
4. ~~Crear modelo ObraAudiovisual (AGAM)~~ ✅

### ✅ Fase 3: Modelos IAAViM - COMPLETADA (v0.5.0)
1. ~~Crear modelo Cinemateca~~ ✅
2. ~~Crear modelo Exhibicion~~ ✅
3. ~~Crear modelo Sala~~ ✅
4. ~~Crear modelo Festival~~ ✅
5. ~~Crear modelo EstudianteESA~~ ✅

### ✅ Fase 4: Endpoints - COMPLETADA (v0.4.0 - v0.5.0)
1. ~~CRUD para cada modelo~~ ✅
2. Endpoints de búsqueda y filtrado ⏳
3. Endpoints de reportes ⏳
4. Upload de archivos/documentación ⏳

### ⏳ Fase 5: Integración - PENDIENTE
1. Conectar formularios del frontend con API
2. Implementar validaciones server-side
3. Manejo de archivos (documentación, certificados)
4. Testing E2E

---

## 7. Recomendaciones de Mejora (v0.5.3)

### 7.1 Seguridad
- [x] ~~Configurar CORS específico por entorno~~ ✅ v0.2.0
- [x] ~~Remover prints de debug~~ ✅ v0.2.0
- [ ] Implementar rate limiting
- [ ] No exponer hashes en tokens de recuperación
- [ ] Implementar refresh token endpoint

### 7.2 Código
- [x] ~~Fijar versiones en requirements.txt~~ ✅ v0.5.1
- [x] ~~Corregir typo `admin_training_rutes.py`~~ ✅ v0.5.1
- [x] ~~Migrar de `on_event` a `lifespan`~~ ✅ v0.5.2
- [x] ~~Corregir deprecation warnings Pydantic v2~~ ✅ v0.5.2
- [x] ~~Agregar tests unitarios~~ ✅ v0.5.0 (33 tests)
- [x] ~~Documentar endpoints con OpenAPI~~ ✅ (Swagger automático)
- [ ] Corregir typo `trainig_schemas.py`

### 7.3 Base de Datos
- [x] ~~Agregar migraciones con Alembic~~ ✅ v0.5.3
- [x] ~~Agregar timestamps a modelos nuevos~~ ✅ v0.5.0
- [ ] Crear índices para búsquedas frecuentes
- [ ] Implementar soft delete consistente

### 7.4 DevOps
- [ ] Implementar health checks
- [ ] Configurar logging estructurado
- [ ] Agregar métricas y monitoreo

---

## 8. Priorización de Tareas (v0.5.3)

### ✅ Tareas Completadas (15/15)
| # | Tarea | Versión |
|---|-------|---------|
| 1 | Corregir bugs críticos | v0.2.0 |
| 2 | Completar modelo PersonaFisica | v0.3.0 |
| 3 | Crear modelo PersonaJuridica | v0.3.0 |
| 4 | Crear modelo Asociacion | v0.3.0 |
| 5 | Crear modelo ObraAudiovisual | v0.3.0 |
| 6 | Configurar CORS por entorno | v0.2.0 |
| 7 | Remover prints de debug | v0.2.0 |
| 8 | Crear modelos ESA/Exhibiciones/Cinemateca | v0.5.0 |
| 9 | Agregar tests con pytest | v0.5.0 |
| 10 | Migrar tests a PostgreSQL (testcontainers) | v0.5.1 |
| 11 | Fijar versiones de dependencias | v0.5.1 |
| 12 | Corregir typo `admin_training_rutes.py` | v0.5.1 |
| 13 | Corregir deprecation warnings Pydantic v2 | v0.5.2 |
| 14 | Migrar `on_event` a `lifespan` handlers | v0.5.2 |
| 15 | Implementar Alembic (migraciones) | v0.5.3 |

### ⏳ Tareas Pendientes
| # | Prioridad | Tarea | Esfuerzo | Impacto |
|---|-----------|-------|----------|---------|
| 1 | 🟢 Baja | Implementar health checks | Bajo | Medio |
| 2 | 🟢 Baja | Configurar logging estructurado | Medio | Medio |
| 3 | 🟢 Baja | Corregir typo `trainig_schemas.py` | Bajo | Bajo |

---

## 9. Estado Actual del Backend (v0.5.3)

### 📊 Resumen
```
✅ Backend 100% operativo en Docker (localhost:8000)
✅ Swagger UI disponible (/docs)
✅ 9 formularios/módulos RePA implementados
✅ Autenticación JWT funcionando
✅ CORS configurado por entorno
✅ 33/33 tests pasando (100%)
✅ Tests con PostgreSQL real (testcontainers)
✅ Migraciones con Alembic configuradas
✅ Deprecation warnings corregidos (24 warnings restantes de SQLAlchemy)
```

### 🧪 Suite de Tests
| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_auth.py` | 9 | ✅ 9/9 passed |
| `test_persona_fisica.py` | 9 | ✅ 9/9 passed |
| `test_esa.py` | 6 | ✅ 6/6 passed |
| `test_exhibiciones.py` | 9 | ✅ 9/9 passed |
| **Total** | **33** | **✅ 33/33 passed** |

### 📁 Modelos Implementados
| Modelo | Archivo | Tablas |
|--------|---------|--------|
| User + Roles | `user_models.py` | `users`, `roles`, `user_roles`, `token_recovery` |
| PersonaFisica | `persona_fisica_model.py` | `personas_fisicas` + 8 subperfiles |
| PersonaJuridica | `persona_juridica_model.py` | `personas_juridicas`, `integrantes_pj` |
| Asociacion | `asociacion_model.py` | `asociaciones`, `integrantes_asociacion` |
| ObraAudiovisual | `obra_audiovisual_model.py` | `obras_audiovisuales`, `equipo_tecnico_obra` |
| EstudianteESA | `esa_model.py` | `estudiantes_esa` |
| Exhibiciones | `exhibicion_model.py` | `salas`, `exhibiciones`, `festivales`, `cinemateca` |
| Training | `training_models.py` | `trainings` |
| Work | `work_models.py` | `trabajos`, `rol_at_work`, `tareas_at_work` |

### 🔗 Endpoints Disponibles
| Prefijo | Descripción | Métodos |
|---------|-------------|---------|
| `/users` | Autenticación y perfil | 8 endpoints |
| `/admin_user` | Administración de usuarios | 5 endpoints |
| `/persona-fisica` | Formulario PF | 20+ endpoints |
| `/persona-juridica` | Formulario PJ | 8 endpoints |
| `/asociacion` | Formulario AS | 8 endpoints |
| `/obras` | AGAM | 10 endpoints |
| `/esa` | Estudiantes ESA | 6 endpoints |
| `/exhibiciones` | Exhibiciones, Salas, Festivales, Cinemateca | 16 endpoints |
| `/training` | Capacitaciones | 5 endpoints |
| `/work` | Trabajos | 7 endpoints |

---

*Documento generado el 23/01/2026*
*Última actualización: 24/01/2026 10:30*
*Versión del backend analizada: 0.5.3*
