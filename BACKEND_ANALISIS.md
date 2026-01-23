# Análisis del Backend RePA 2025

## Resumen Ejecutivo

El backend de RePA 2025 es una API REST desarrollada en **FastAPI** con **PostgreSQL** como base de datos, utilizando **SQLAlchemy** como ORM. Implementa autenticación JWT con sistema de roles y permisos.

**Estado actual:** MVP funcional con módulos de usuarios, capacitaciones y trabajos. Falta integración con los formularios del frontend (Persona Física, Persona Jurídica, Asociación/Colectivo, AGAM, ESA, Cinemateca, Exhibiciones).

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

### 1.2 Estructura de Directorios
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
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── user_models.py
│   │   ├── person_model.py
│   │   ├── training_models.py
│   │   └── work_models.py
│   ├── schemas/             # Esquemas Pydantic
│   │   ├── user_schemas.py
│   │   ├── person_schema.py
│   │   ├── trainig_schemas.py
│   │   └── work_schemas.py
│   └── routes/              # Endpoints API
│       ├── user_routes.py
│       ├── admin_routes.py
│       ├── training_routes.py
│       ├── admin_training_rutes.py
│       ├── person_routes.py
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

### 4.1 🔴 Críticos

#### 4.1.1 CORS Abierto a Todos
```python
# main.py línea 28
origin = ['*']  # ⚠️ Permite cualquier origen
```
**Riesgo:** Vulnerabilidad de seguridad en producción.
**Solución:** Configurar orígenes específicos por entorno.

#### 4.1.2 Modelo Person con Import Incorrecto
```python
# person_model.py línea 4
from src.db.database import Base  # ⚠️ Ruta incorrecta
# Debería ser:
from src.database import Base
```
**Impacto:** El modelo Person no se puede usar.

#### 4.1.3 Modelo Person con FK Incorrecta
```python
# person_model.py línea 10
user_email = Column(String, ForeignKey("users.email"))  # ⚠️ Debería ser user_id
```
**Impacto:** Relación incorrecta con usuarios.

#### 4.1.4 Variable `db` No Definida en `/me`
```python
# user_routes.py línea 300
user = db.query(User).filter(...)  # ⚠️ db no está definida
# Falta: db: Session = Depends(get_db)
```
**Impacto:** Endpoint `/users/me` GET no funciona.

#### 4.1.5 Bug en training_routes.py
```python
# training_routes.py línea 119
if not training:  # ⚠️ Debería ser 'trainings'
```
**Impacto:** Error de referencia en listado de capacitaciones.

### 4.2 🟡 Importantes

#### 4.2.1 Prints de Debug en Producción
```python
# utils.py, user_routes.py, token_utils.py
print(f"Utils - get_current_user - payload: {payload}")  # Debug
print(f"URL de verificación: {verification_url}")
```
**Riesgo:** Exposición de información sensible en logs.
**Solución:** Usar logger con niveles apropiados.

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

### 5.1 Comparación Frontend vs Backend

| Formulario Frontend | Modelo Backend | Estado |
|---------------------|----------------|--------|
| **Persona Física (PF)** | Person (parcial) | 🟡 Incompleto |
| **Persona Jurídica (PJ)** | - | 🔴 No existe |
| **Asociación/Colectivo (AS)** | - | 🔴 No existe |
| **AGAM (Obras)** | - | 🔴 No existe |
| **ESA (Estudiantes)** | - | 🔴 No existe |
| **Cinemateca** | - | 🔴 No existe |
| **Exhibiciones** | - | 🔴 No existe |
| **Salas de Exhibición** | - | 🔴 No existe |
| **Festivales** | - | 🔴 No existe |

### 5.2 Modelos Requeridos

#### Persona Física (Ampliación)
```python
# Campos faltantes según frontend:
- subperfiles (productor, director, guionista, etc.)
- situacion_laboral
- interes_institucional
- consentimiento
- documentacion (archivos)
```

#### Persona Jurídica
```python
class PersonaJuridica(Base):
    __tablename__ = "personas_juridicas"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    razon_social = Column(String, nullable=False)
    cuit = Column(String, unique=True, nullable=False)
    tipo_sociedad = Column(String)
    fecha_constitucion = Column(Date)
    objeto_social = Column(Text)
    # domicilio, contacto, representante legal...
    # integrantes vinculados al REPA
    # actividades audiovisuales
    # documentacion
```

#### Asociación/Colectivo
```python
class Asociacion(Base):
    __tablename__ = "asociaciones"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    nombre = Column(String, nullable=False)
    fecha_inicio_actividades = Column(Date)
    # ambitos de actuacion
    # integrantes vinculados al REPA
    # documentacion
```

#### AGAM (Obras Audiovisuales)
```python
class ObraAudiovisual(Base):
    __tablename__ = "obras_audiovisuales"
    id = Column(Integer, primary_key=True)
    codigo_agam = Column(String, unique=True)
    titulo = Column(String, nullable=False)
    titulo_original = Column(String)
    anio_produccion = Column(Integer)
    tipo_obra = Column(String)  # largo, corto, serie, etc.
    genero = Column(String)
    duracion_minutos = Column(Integer)
    sinopsis = Column(Text)
    # datos técnicos
    # datos relacionales (director, productor, etc.)
    # derechos
```

#### Cinemateca
```python
class RegistroCinemateca(Base):
    __tablename__ = "registros_cinemateca"
    id = Column(Integer, primary_key=True)
    obra_id = Column(Integer, ForeignKey("obras_audiovisuales.id"))
    tipo_soporte = Column(String)
    estado_conservacion = Column(String)
    ubicacion_fisica = Column(String)
    # prestamos
```

#### Exhibiciones
```python
class Exhibicion(Base):
    __tablename__ = "exhibiciones"
    id = Column(Integer, primary_key=True)
    obra_id = Column(Integer, ForeignKey("obras_audiovisuales.id"))
    sala_id = Column(Integer, ForeignKey("salas.id"))
    fecha_exhibicion = Column(Date)
    cantidad_funciones = Column(Integer)
    espectadores_total = Column(Integer)
    # desglose por tipo de entrada
```

---

## 6. Plan de Integración Frontend-Backend

### 6.1 Fase 1: Correcciones Críticas
1. Corregir import en `person_model.py`
2. Corregir FK de Person (user_email → user_id)
3. Agregar `db` dependency en `/users/me` GET
4. Corregir bug en `training_routes.py`
5. Configurar CORS por entorno

### 6.2 Fase 2: Modelos Base
1. Completar modelo Person con campos del frontend
2. Crear modelo PersonaJuridica
3. Crear modelo Asociacion
4. Crear modelo ObraAudiovisual (AGAM)

### 6.3 Fase 3: Modelos IAAViM
1. Crear modelo RegistroCinemateca
2. Crear modelo Exhibicion
3. Crear modelo Sala
4. Crear modelo Festival

### 6.4 Fase 4: Endpoints
1. CRUD para cada modelo
2. Endpoints de búsqueda y filtrado
3. Endpoints de reportes
4. Upload de archivos/documentación

### 6.5 Fase 5: Integración
1. Conectar formularios del frontend con API
2. Implementar validaciones server-side
3. Manejo de archivos (documentación, certificados)
4. Testing E2E

---

## 7. Recomendaciones de Mejora

### 7.1 Seguridad
- [ ] Configurar CORS específico por entorno
- [ ] Remover prints de debug
- [ ] Implementar rate limiting
- [ ] Agregar validación de entrada más estricta
- [ ] No exponer hashes en tokens
- [ ] Implementar refresh token endpoint

### 7.2 Código
- [ ] Fijar versiones en requirements.txt
- [ ] Corregir typos en nombres de archivos
- [ ] Unificar nomenclatura de modelos/schemas
- [ ] Migrar de `on_event` a `lifespan`
- [ ] Agregar tests unitarios
- [ ] Documentar endpoints con OpenAPI

### 7.3 Base de Datos
- [ ] Agregar migraciones con Alembic
- [ ] Crear índices para búsquedas frecuentes
- [ ] Implementar soft delete consistente
- [ ] Agregar timestamps (created_at, updated_at) a todos los modelos

### 7.4 DevOps
- [ ] Separar configuración por entorno (dev/staging/prod)
- [ ] Implementar health checks
- [ ] Configurar logging estructurado
- [ ] Agregar métricas y monitoreo

---

## 8. Priorización de Tareas

| # | Prioridad | Tarea | Esfuerzo | Impacto |
|---|-----------|-------|----------|---------|
| 1 | 🔴 Alta | Corregir bugs críticos (4.1) | Bajo | Crítico |
| 2 | 🔴 Alta | Completar modelo Person | Medio | Alto |
| 3 | 🔴 Alta | Crear modelo PersonaJuridica | Medio | Alto |
| 4 | 🔴 Alta | Crear modelo Asociacion | Medio | Alto |
| 5 | 🔴 Alta | Crear modelo ObraAudiovisual | Alto | Alto |
| 6 | 🟡 Media | Configurar CORS por entorno | Bajo | Alto |
| 7 | 🟡 Media | Remover prints de debug | Bajo | Medio |
| 8 | 🟡 Media | Implementar Alembic | Medio | Alto |
| 9 | 🟡 Media | Crear modelos Cinemateca/Exhibiciones | Alto | Medio |
| 10 | 🟢 Baja | Fijar versiones de dependencias | Bajo | Bajo |
| 11 | 🟢 Baja | Corregir typos en archivos | Bajo | Bajo |
| 12 | 🟢 Baja | Agregar tests | Alto | Alto |

---

*Documento generado el 23/01/2026*
*Versión del backend analizada: 0.1.0*
