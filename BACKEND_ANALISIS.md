# Análisis del Backend RePA 2025

## Resumen Ejecutivo

El backend de RePA 2025 es una API REST desarrollada en **FastAPI** con **PostgreSQL** como base de datos, utilizando **SQLAlchemy** como ORM. Implementa autenticación JWT con sistema de roles y permisos.

**Estado actual (v0.4.0):** Backend operativo con módulos de usuarios, capacitaciones, trabajos y **formularios RePA completos** (Persona Física, Persona Jurídica, Asociación/Colectivo, AGAM). Pendiente: ESA, Cinemateca, Exhibiciones.

---

## 1. Arquitectura y Estructura

### 1.1 Stack Tecnológico
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | latest |
| ORM | SQLAlchemy | latest |
| Base de datos | PostgreSQL | latest |
| Autenticación | JWT (python-jose) | latest |
| Hashing | bcrypt/passlib | 1.7.4/3.2.0 |
| Validación | Pydantic | latest |
| Contenedores | Docker | 3 |

### 1.2 Estructura de Directorios (Actualizada v0.4.0)
```
backend/
├── src/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── database.py          # Configuración SQLAlchemy
│   ├── seed.py              # Datos iniciales (roles)
│   ├── utils.py             # Utilidades (auth, validaciones)
│   ├── token_utils.py       # Manejo de JWT
│   ├── logger.py            # Configuración de logs
│   ├── middlewarelogg.py    # Middleware de logging
│   ├── .env                 # Variables de entorno (CORS_ORIGINS)
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── __init__.py           # ✅ Registro centralizado
│   │   ├── user_models.py
│   │   ├── persona_fisica_model.py    # ✅ NUEVO (reemplaza person_model.py)
│   │   ├── persona_juridica_model.py  # ✅ NUEVO
│   │   ├── asociacion_model.py        # ✅ NUEVO
│   │   ├── obra_audiovisual_model.py  # ✅ NUEVO (AGAM)
│   │   ├── training_models.py
│   │   └── work_models.py
│   ├── schemas/             # Esquemas Pydantic
│   │   ├── user_schemas.py
│   │   ├── persona_fisica_schemas.py    # ✅ NUEVO
│   │   ├── persona_juridica_schemas.py  # ✅ NUEVO
│   │   ├── asociacion_schemas.py        # ✅ NUEVO
│   │   ├── obra_audiovisual_schemas.py  # ✅ NUEVO
│   │   ├── trainig_schemas.py
│   │   └── work_schemas.py
│   └── routes/              # Endpoints API
│       ├── user_routes.py
│       ├── admin_routes.py
│       ├── persona_fisica_routes.py     # ✅ NUEVO
│       ├── persona_juridica_routes.py   # ✅ NUEVO
│       ├── asociacion_routes.py         # ✅ NUEVO
│       ├── obra_audiovisual_routes.py   # ✅ NUEVO
│       ├── training_routes.py
│       ├── admin_training_rutes.py
│       └── work_routes.py
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

## 4. Observaciones y Problemas Detectados

### 4.1 🔴 Críticos (TODOS RESUELTOS ✅)

#### 4.1.1 ~~CORS Abierto a Todos~~ ✅ CORREGIDO v0.2.0
```python
# main.py - Ahora usa variable de entorno CORS_ORIGINS
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
```
**Estado:** Configurado en `.env` con `CORS_ORIGINS`.

#### 4.1.2 ~~Modelo Person con Import Incorrecto~~ ✅ CORREGIDO v0.3.0
**Estado:** Archivo `person_model.py` eliminado y reemplazado por `persona_fisica_model.py`.

#### 4.1.3 ~~Modelo Person con FK Incorrecta~~ ✅ CORREGIDO v0.3.0
**Estado:** Nuevo modelo `PersonaFisica` con FK correcta a `users.id`.

#### 4.1.4 ~~Variable `db` No Definida en `/me`~~ ✅ CORREGIDO v0.2.0
```python
# user_routes.py - Ahora incluye dependency
async def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
```

#### 4.1.5 ~~Bug en training_routes.py~~ ✅ CORREGIDO v0.2.0
```python
# training_routes.py línea 119 - Corregido
if not trainings:  # ✅ Variable correcta
```

### 4.2 🟡 Importantes

#### 4.2.1 ~~Prints de Debug en Producción~~ ✅ CORREGIDO v0.2.0
```python
# utils.py - Ahora usa logger.debug()
logger.debug(f"get_current_user - payload: {payload}")
```
**Estado:** Prints reemplazados por `logger.debug()` en `utils.py`, `user_routes.py` y `seed.py`.

#### 4.2.2 Typos en Nombres de Archivos
- `admin_training_rutes.py` → debería ser `admin_training_routes.py`
- `trainig_schemas.py` → debería ser `training_schemas.py`

#### 4.2.3 Inconsistencia en Nombres de Modelos
```python
# work_routes.py usa RolAtWork y TareaAtWork (schemas)
# Pero los modelos son RolWork y TareaWork
```

#### 4.2.4 Falta Validación de Email Único en Update
```python
# user_routes.py línea 323-324
if user_in.email:
    user.email = user_in.email  # ⚠️ No verifica duplicados
```

#### 4.2.5 Token de Recuperación Expone Password Hasheado
```python
# user_routes.py línea 237
registration_token = create_access_token(
    data={"sub": user.id, "new_password": hashed_password},  # ⚠️ Inseguro
```
**Riesgo:** El hash de la contraseña viaja en el token.

### 4.3 🟢 Menores

#### 4.3.1 Dependencias Sin Versiones Fijas
```txt
# requirements.txt
fastapi
uvicorn
sqlalchemy
```
**Riesgo:** Incompatibilidades futuras.
**Solución:** Fijar versiones específicas.

#### 4.3.2 Falta Endpoint de Refresh Token
El login genera `refresh_token` pero no hay endpoint para usarlo.

#### 4.3.3 Deprecation Warning
```python
# main.py línea 40
@app.on_event("startup")  # ⚠️ Deprecado en FastAPI 0.100+
```
**Solución:** Usar `lifespan` context manager.

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

## 7. Recomendaciones de Mejora (Actualizado v0.5.0)

### 7.1 Seguridad
- [x] ~~Configurar CORS específico por entorno~~ ✅ v0.2.0
- [x] ~~Remover prints de debug~~ ✅ v0.2.0
- [ ] Implementar rate limiting
- [ ] Agregar validación de entrada más estricta
- [ ] No exponer hashes en tokens
- [ ] Implementar refresh token endpoint

### 7.2 Código
- [ ] Fijar versiones en requirements.txt
- [ ] Corregir typos en nombres de archivos (`admin_training_rutes.py`)
- [ ] Unificar nomenclatura de modelos/schemas
- [ ] Migrar de `on_event` a `lifespan`
- [x] ~~Agregar tests unitarios~~ ✅ v0.5.0 (30 tests)
- [x] ~~Documentar endpoints con OpenAPI~~ ✅ (Swagger automático)
- [ ] Corregir deprecation warnings de Pydantic v2

### 7.3 Base de Datos
- [ ] Agregar migraciones con Alembic
- [ ] Crear índices para búsquedas frecuentes
- [ ] Implementar soft delete consistente
- [x] ~~Agregar timestamps a modelos nuevos~~ ✅ v0.5.0 (ESA, Exhibiciones)

### 7.4 DevOps
- [ ] Separar configuración por entorno (dev/staging/prod)
- [ ] Implementar health checks
- [ ] Configurar logging estructurado
- [ ] Agregar métricas y monitoreo

---

## 8. Priorización de Tareas (Actualizado v0.5.0)

### ✅ Tareas Completadas
| # | Tarea | Versión |
|---|-------|---------|
| 1 | ~~Corregir bugs críticos (4.1)~~ | v0.2.0 |
| 2 | ~~Completar modelo PersonaFisica~~ | v0.3.0 |
| 3 | ~~Crear modelo PersonaJuridica~~ | v0.3.0 |
| 4 | ~~Crear modelo Asociacion~~ | v0.3.0 |
| 5 | ~~Crear modelo ObraAudiovisual~~ | v0.3.0 |
| 6 | ~~Configurar CORS por entorno~~ | v0.2.0 |
| 7 | ~~Remover prints de debug~~ | v0.2.0 |
| 8 | ~~Crear modelos ESA/Exhibiciones/Cinemateca~~ | v0.5.0 |
| 9 | ~~Agregar tests~~ | v0.5.0 |
| 10 | ~~Migrar tests a PostgreSQL (testcontainers)~~ | v0.5.1 |
| 11 | ~~Fijar versiones de dependencias~~ | v0.5.1 |
| 12 | ~~Corregir typo `admin_training_rutes.py`~~ | v0.5.1 |
| 13 | ~~Corregir deprecation warnings Pydantic v2~~ | v0.5.2 |
| 14 | ~~Migrar `on_event` a `lifespan` handlers~~ | v0.5.2 |

### ⏳ Tareas Pendientes
| # | Prioridad | Tarea | Esfuerzo | Impacto |
|---|-----------|-------|----------|---------|
| 1 | 🟡 Media | Implementar Alembic (migraciones) | Medio | Alto |
| 2 | � Baja | Implementar health checks | Bajo | Medio |
| 3 | 🟢 Baja | Configurar logging estructurado | Medio | Medio |

---

*Documento generado el 23/01/2026*
*Última actualización: 24/01/2026 10:20*
*Versión del backend analizada: 0.5.2*

---

## 9. Resumen de Cambios Realizados (v0.2.0 - v0.5.0)

### ✅ Bugs Críticos Corregidos (v0.2.0)
| Bug | Archivo | Solución |
|-----|---------|----------|
| CORS wildcard | `main.py` | Variable de entorno `CORS_ORIGINS` |
| Import incorrecto | `person_model.py` | Eliminado, reemplazado por `persona_fisica_model.py` |
| FK incorrecta | `person_model.py` | Nuevo modelo con `user_id` correcto |
| `db` no definida | `user_routes.py` | Agregada dependency `Depends(get_db)` |
| Variable `training` | `training_routes.py` | Corregido a `trainings` |
| Prints de debug | Varios | Reemplazados por `logger.debug()` |

### ✅ Modelos Creados (v0.3.0)
| Modelo | Tablas | Descripción |
|--------|--------|-------------|
| `PersonaFisica` | `personas_fisicas` + 8 subperfiles | Formulario PF completo |
| `PersonaJuridica` | `personas_juridicas` + `integrantes_pj` | Formulario PJ completo |
| `Asociacion` | `asociaciones` + `integrantes_asociacion` | Formulario AS completo |
| `ObraAudiovisual` | `obras_audiovisuales` + `equipo_tecnico_obra` | Formulario AGAM completo |

### ✅ Schemas y Rutas (v0.4.0)
| Endpoint | Métodos | Descripción |
|----------|---------|-------------|
| `/persona-fisica` | CRUD + subperfiles | 20+ endpoints |
| `/persona-juridica` | CRUD + integrantes | 8 endpoints |
| `/asociacion` | CRUD + integrantes | 8 endpoints |
| `/obras` | CRUD + equipo técnico | 10 endpoints |

### ✅ Modelos ESA y Exhibiciones (v0.5.0)
| Modelo | Tabla | Descripción |
|--------|-------|-------------|
| `EstudianteESA` | `estudiantes_esa` | Registro estudiantes audiovisual (vigencia 1 año) |
| `Sala` | `salas` | Salas de exhibición con características técnicas |
| `Exhibicion` | `exhibiciones` | Registro de proyecciones y espectadores |
| `Festival` | `festivales` | Festivales de cine con categorías |
| `Cinemateca` | `cinemateca` | Gestión archivo físico de obras |

### ✅ Rutas Nuevas (v0.5.0)
| Endpoint | Métodos | Descripción |
|----------|---------|-------------|
| `/esa` | CRUD + renovación | Estudiantes ESA |
| `/exhibiciones` | CRUD | Exhibiciones |
| `/exhibiciones/salas` | CRUD | Salas de exhibición |
| `/exhibiciones/festivales` | CRUD | Festivales |
| `/exhibiciones/cinemateca` | CRUD | Cinemateca |

### ✅ Suite de Tests (v0.5.0)
| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_auth.py` | 9 | 7 passed, 2 skipped |
| `test_persona_fisica.py` | 9 | ✅ passed |
| `test_esa.py` | 7 | ✅ passed |
| `test_exhibiciones.py` | 10 | 9 passed, 1 failed |
| **Total** | **35** | **30 passed, 2 skipped, 3 failed** |

### 📊 Estado Actual del Backend (v0.5.0)
```
✅ Operativo en Docker (localhost:8000)
✅ Swagger UI disponible (/docs)
✅ 9 formularios/módulos RePA implementados
✅ Autenticación JWT funcionando
✅ CORS configurado por entorno
✅ Suite de tests configurada (pytest)
✅ 85% tests pasando (30/35)

⏳ Pendiente: Migraciones con Alembic
⏳ Pendiente: Mejorar configuración de tests (SQLite vs PostgreSQL)
⏳ Pendiente: Deprecation warnings de Pydantic v2
```

### 🔧 Warnings Detectados
- **Pydantic**: `class Config` deprecado → migrar a `ConfigDict`
- **FastAPI**: `on_event` deprecado → migrar a `lifespan` handlers
