# Propuesta de Estructura de Datos para REPA

**REPA - IAAviM**
20 de Febrero del 2025

## VISIÓN GENERAL

Definición de la estructura de datos propuesta para REPA.

## OBJETIVOS

*   Definir un esquema de estructura de datos.
*   Definir la relación de la estructura de datos.

## ESPECIFICACIONES

La estructura de datos propuesta se ha extraído de la documentación disponible de los reportes de REPA-IAAviM. Se utiliza la nomenclatura basada en FastAPI + sqlalchemy.

## HITOS

Estructura de datos propuesta

## Estructura de datos propuesta

### models/user_model.py

```python
class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")  # Define roles: admin, editor, viewer, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=None, nullable=True)
    person = relationship("Person", back_populates="user", uselist=False) # Relación 1:1 con Person
    company = relationship("Company", back_populates="user", uselist=False) # Relación 1:N con Company
    trainings = relationship("Training", back_populates="user")  # Relación 1:N con Training
    audiovisual_works = relationship("AudiovisualWork", back_populates="user")  # Relación 1:N con AudiovisualWork
```

### models/person_model.py

```python
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), unique=True, nullable=False)  # Relación 1 a 1
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni_cuit_cuil = Column(String, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    nacionalidad = Column(String, nullable=True)
    identidad_genero = Column(String, nullable=True)
    etnia = Column(Boolean, default=True)
    etnia_nombre = Column(String, nullable=True)
    estado_civil = Column(String, nullable=True)
    educacion_nivel = Column(String, nullable=True)
    educacion_titulo = Column(String, nullable=True)
    educacion_institucion = Column(String, nullable=True)
    personas_a_cargo = Column(Integer, default=0)
    tipo_contribuyente = Column(String, nullable=True)
    actividad_registrada = Column(String, nullable=True)
    telefono = Column(String, nullable=False)
    dir_calle = Column(String, nullable=True)
    dir_numero = Column(String, nullable=True)
    dir_piso = Column(String, nullable=True)
    dir_letra_nro_depto = Column(String, nullable=True)
    dir_cp = Column(String, nullable=True)
    dir_localidad = Column(String, nullable=True)
    dir_departamento = Column(String, nullable=True)
    dir_provincia = Column(String, nullable=True)
    dir_pais = Column(String, nullable=True)
    # Relación con el usuario
    user = relationship("User", back_populates="person")
```

### models/company_model.py

```python
class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    start_year = Column(Date, nullable=False)
    cuit = Column(String, nullable=False, unique=True)
    legal_status = Column(String, nullable=False)
    annual_revenue = Column(Integer, nullable=True)
    fixed_employees = Column(Integer, nullable=True)
    temporary_employees = Column(Integer, nullable=True)
    productions = Column(Integer, nullable=True)
    funding_source = Column(String, nullable=True)
    user_email = Column(String, ForeignKey("users.email"))
    user = relationship("User", back_populates="company")
```

### models/collaborator_model.py

```python
class Collaborator(Base):
    __tablename__ = "collaborators"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    dni_cuil = Column(String, unique=True, nullable=False)
    role_description = Column(String, nullable=False)
    audiovisual_work_id = Column(Integer, ForeignKey("audiovisual_works.id"))
    audiovisual_work = relationship("AudiovisualWork", back_populates="collaborators")
```

### models/audiovisual_work_model.py

```python
class AudiovisualWork(Base):
    __tablename__ = "audiovisual_works"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)  # Relación con el usuario
    rol = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    formato = Column(String, nullable=False)
    formato_descripcion = Column(String, nullable=True)
    tipo_produccion = Column(String, nullable=False)
    genero = Column(String, nullable=False)
    genero_descripcion = Column(String, nullable=True)
    clasificacion = Column(String, nullable=False)
    lugar = Column(String, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    idioma_original = Column(String, nullable=False)
    subtitulos_idioma = Column(String, nullable=True)
    doblaje_idioma = Column(String, nullable=True)
    capitulo_numero = Column(Integer, default=1)
    capitulo_duracion = Column(Integer, default=0)
    resolucion_video = Column(String, default="1920x1080Px", nullable=True)
    audio_tipo = Column(String, default="5.1 - 7.1 Stereo", nullable=True)
    estreno_fecha = Column(Date, nullable=True)
    sinopsis = Column(String, nullable=True)
    storyline = Column(String, nullable=True)
    avant_premier = Column(String, nullable=True)
    avant_premier_iaavim = Column(Boolean, default=False)
    exhibicion = Column(String, nullable=True)
    valoracion_agam = Column(Integer, nullable=True)
    fondos_propios = Column(String, nullable=True)
    asociados_nacionales = Column(String, nullable=True)
    asociados_internacionales = Column(String, nullable=True)
    fondos_iaavim = Column(String, nullable=True)
    fondos_inca = Column(String, nullable=True)
    fondos_gubernamental = Column(String, nullable=True)
    fondos_internacionales = Column(String, nullable=True)
    venta_nacional = Column(String, nullable=True)
    venta_internacional = Column(String, nullable=True)
    # Relación con el usuario
    user_email = Column(String, ForeignKey("users.email"))
    user = relationship("User", back_populates="audiovisual_works")
    collaborators = relationship("Collaborator", back_populates="audiovisual_work")
```

### models/training_model.py

```python
class Training(Base):
    __tablename__ = "trainings"
    id = Column(Integer, primary_key=True, index
```

### Detalle Estructura de datos:

1 User --> 1 Person

1 User --> N Company

1 User --> N Training

1 User --> N Audiovisual_Work

1 Audiovisual_Work --> N Collaborator

1 Audiovisual_Work --> N Audiovisual_Upload
