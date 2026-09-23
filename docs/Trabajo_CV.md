Para diseñar un modelo de datos que registre la experiencia laboral de un usuario en producciones audiovisuales, es esencial capturar información detallada sobre cada proyecto y las funciones desempeñadas. A continuación, se presenta una estructura de base de datos que refleja esta relación de uno a muchos entre usuarios y sus trabajos en el ámbito audiovisual:

### Tablas Principales

1. **Usuarios (`users`)**
   - `id`: Identificador único del usuario.
   - `email`: Dirección de correo electrónico.
   - `hashed_password`: Hash de la contraseña del usuario.
   - `is_active`: Indica si el usuario está activo.
   - `created_at`: Fecha y hora de creación del registro del usuario.
   - `last_login` : Fecha y hora del último inicio de sesión del usuario.
   *Ya está resuelto en el modelo de datos de Usurios* [MODELO_DE_DATOS.md]

2. **Trabajos (`works`)**
   - `id`: Identificador único del trabajo.
   - `usuario_id`: Clave foránea que relaciona el trabajo con el usuario correspondiente.
   - `titulo_produccion`: Nombre de la producción audiovisual.
   - `tipo_produccion`: Tipo de producción (por ejemplo, película, serie, documental, comercial).
   - `fecha_inicio`: Fecha de inicio del trabajo.
   - `fecha_fin`: Fecha de finalización del trabajo.
   - `descripcion`: Descripción detallada de las responsabilidades y logros en el proyecto.
   - `enlace_portafolio`: URL a una muestra del trabajo realizado (si aplica).

3. **Roles (`roles`)**
   - `id`: Identificador único del rol.
   - `nombre`: Nombre del rol desempeñado (por ejemplo, director, productor, editor, guionista).

4. **Tareas (`tasks`)**
   - `id`: Identificador único de la tarea.
   - `nombre`: Nombre de la tarea específica realizada (por ejemplo, edición de video, mezcla de sonido, diseño de iluminación).

5. **Trabajos_Roles (`works_roles`)**
   - `id`: Identificador único de la relación.
   - `trabajo_id`: Clave foránea que relaciona con la tabla `works`.
   - `rol_id`: Clave foránea que indica el rol desempeñado en ese trabajo.

6. **Trabajos_Tareas (`works_tasks`)**
   - `id`: Identificador único de la relación.
   - `trabajo_id`: Clave foránea que relaciona con la tabla `works`.
   - `tarea_id`: Clave foránea que indica la tarea específica realizada en ese trabajo.

### Relaciones y Consideraciones

- **Usuarios y Trabajos**: Relación uno a muchos; un usuario puede tener múltiples trabajos registrados.
- **Trabajos y Roles**: Relación muchos a muchos; un trabajo puede involucrar varios roles, y un rol puede estar presente en múltiples trabajos.
- **Trabajos y Tareas**: Relación muchos a muchos; un trabajo puede incluir diversas tareas específicas, y una tarea puede haberse realizado en distintos trabajos.

Esta estructura permite una representación detallada y flexible de la experiencia laboral en producciones audiovisuales, abarcando la diversidad de roles y tareas que un profesional puede desempeñar en este campo. 

---

Para modelar la estructura propuesta en SQLAlchemy, que refleja la experiencia laboral de un usuario en producciones audiovisuales con múltiples roles y tareas, se pueden definir las siguientes clases:


```python
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Tabla de asociación para la relación muchos a muchos entre Trabajos y Roles
trabajos_roles = Table('trabajos_roles', Base.metadata,
    Column('trabajo_id', Integer, ForeignKey('trabajos.id'), primary_key=True),
    Column('rol_id', Integer, ForeignKey('roles_work.id'), primary_key=True)
)

# Tabla de asociación para la relación muchos a muchos entre Trabajos y Tareas
trabajos_tareas = Table('trabajos_tareas', Base.metadata,
    Column('trabajo_id', Integer, ForeignKey('trabajos.id'), primary_key=True),
    Column('tarea_id', Integer, ForeignKey('tareas_work.id'), primary_key=True)
)

class Usuario(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    ...
    trabajos = relationship('Trabajo', back_populates='usuario')

class Trabajo(Base):
    __tablename__ = 'trabajos'

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    titulo_produccion = Column(String, nullable=False)
    tipo_produccion = Column(String)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    descripcion = Column(String)
    enlace_portafolio = Column(String)

    usuario = relationship('Usuario', back_populates='trabajos')
    roles = relationship('Rol', secondary=trabajos_roles, back_populates='trabajos')
    tareas = relationship('Tarea', secondary=trabajos_tareas, back_populates='trabajos')

class Rol(Base):
    __tablename__ = 'roles_work'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)

    trabajos = relationship('Trabajo', secondary=trabajos_roles, back_populates='roles_work')

class Tarea(Base):
    __tablename__ = 'tareas_work'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)

    trabajos = relationship('Trabajo', secondary=trabajos_tareas, back_populates='tareas_work')
```


**Explicación de las Clases y Relaciones:**

- **Usuario (`usuarios`)**: Representa a los usuarios que registran su experiencia laboral. Tiene una relación uno a muchos con la tabla `trabajos`, indicando que un usuario puede tener múltiples trabajos registrados.

- **Trabajo (`trabajos`)**: Almacena información sobre cada producción en la que ha participado el usuario. Contiene claves foráneas que lo relacionan con el usuario correspondiente y establece relaciones muchos a muchos con las tablas `roles` y `tareas` a través de las tablas de asociación `trabajos_roles` y `trabajos_tareas`, respectivamente.

- **Rol (`roles`)**: Define los diferentes roles que se pueden desempeñar en una producción audiovisual (por ejemplo, director, productor). Tiene una relación muchos a muchos con la tabla `trabajos` mediante la tabla de asociación `trabajos_roles`.

- **Tarea (`tareas`)**: Especifica las distintas tareas que se pueden realizar en una producción (por ejemplo, edición de video, mezcla de sonido). Mantiene una relación muchos a muchos con la tabla `trabajos` a través de la tabla de asociación `trabajos_tareas`.

**Tablas de Asociación:**

- **`trabajos_roles`**: Establece la relación muchos a muchos entre `trabajos` y `roles`, permitiendo que un trabajo tenga múltiples roles y que un rol esté asociado a múltiples trabajos.

- **`trabajos_tareas`**: Define la relación muchos a muchos entre `trabajos` y `tareas`, facilitando que un trabajo incluya diversas tareas y que una tarea pueda estar presente en múltiples trabajos.

Esta estructura permite una representación detallada y flexible de la experiencia laboral en producciones audiovisuales, capturando la diversidad de roles y tareas que un profesional puede desempeñar en este ámbito.

---

Para definir los esquemas de datos (schemas) que reflejen la estructura de los modelos SQLAlchemy proporcionados, utilizaremos Pydantic. Pydantic nos permite crear modelos de datos que validan y documentan la información que nuestra API manejará. Estos esquemas serán esenciales para interactuar con FastAPI y garantizar la integridad de los datos.

A continuación, se presentan los esquemas correspondientes a cada modelo:


```python
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import date

class RolAtWorkBase(BaseModel):
    nombre: str

class RolAtWorkCreate(RolAtWorkBase):
    pass

class RolAtWork(RolAtWorkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TareaAtWorkBase(BaseModel):
    nombre: str

class TareaAtWorkCreate(TareaAtWorkBase):
    pass

class TareaAtWork(TareaAtWorkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TrabajoBase(BaseModel):
    titulo_produccion: str
    tipo_produccion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    descripcion: Optional[str] = None
    enlace_portafolio: Optional[str] = None

class TrabajoCreate(TrabajoBase):
    roles: List[RolAtWorkCreate]
    tareas: List[TareaAtWorkCreate]

class Trabajo(TrabajoBase):
    id: int
    usuario_id: int
    roles: List[RolAtWork]
    tareas: List[TareaAtWork]

    model_config = ConfigDict(from_attributes=True)
```


**Detalles de los Esquemas:**

- **`RolAtWorkBase` y `TareaAtWorkBase`**: Definen los atributos básicos (`nombre`) para los roles y tareas, respectivamente.

- **`RolAtWorkCreate` y `TareaAtWorkCreate`**: Extienden las bases correspondientes y se utilizan al crear nuevos roles o tareas.

- **`RolAtWork` y `TareaAtWork`**: Añaden el atributo `id` y configuran `from_attributes=True` (anteriormente `orm_mode=True` en Pydantic v1) para permitir la conversión desde modelos ORM de SQLAlchemy.

- **`TrabajoBase`**: Contiene los atributos principales de un trabajo, incluyendo detalles de la producción y fechas.

- **`TrabajoCreate`**: Extiende `TrabajoBase` e incluye listas de roles y tareas a crear junto con el trabajo.

- **`Trabajo`**: Añade el atributo `id`, `usuario_id` y las listas de roles y tareas asociadas, configurando `from_attributes=True` para la compatibilidad con SQLAlchemy.

**Consideraciones Importantes:**

- Al definir relaciones muchos a muchos, como las existentes entre `Trabajo` y `RolAtWork` o `TareaAtWork`, es esencial manejar adecuadamente las asociaciones en los esquemas para reflejar las relaciones establecidas en los modelos de SQLAlchemy.

- La configuración `from_attributes=True` en la clase `Config` de cada esquema permite que Pydantic trabaje directamente con las instancias de los modelos de SQLAlchemy, facilitando la conversión entre modelos ORM y esquemas Pydantic.

Estos esquemas proporcionan una estructura clara y validada para los datos que manejará tu aplicación, asegurando coherencia y facilitando la integración con FastAPI.