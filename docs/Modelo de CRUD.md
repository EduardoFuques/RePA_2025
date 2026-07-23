## Estructura de implementación

Aquí tienes un ejemplo de una aplicación CRUD con FastAPI y SQLAlchemy para la gestión de usuarios con las características que mencionas. El código está estructurado en cuatro módulos principales: Schemas, Routes, Models, y DB.
Estructura del Proyecto


```
my_app/
├── main.py
├── db/
│   ├── database.py
├── models/
│   ├── user_model.py
├── schemas/
│   ├── user_schema.py
├── routes/
│   ├── user_routes.py
└── requirements.txt

```

1. Archivo principal (main.py)


```
from fastapi import FastAPI
from routes.user_routes import user_router
from db.database import Base, engine

# Crear tablas en la base de datos

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Incluir rutas
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "API de Gestión de Usuarios funcionando correctamente"}

```

2. Base de datos (db/database.py)


```
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost:5432/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para obtener sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```

3. Modelos (models/user_model.py)


```
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=None, nullable=True)
    is_admin = Column(Boolean, default=False)

```

4. Esquemas (schemas/user_schema.py)

```
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_admin: bool

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    created_at: datetime
    last_login: Optional[datetime]

```

5. Rutas (routes/user_routes.py)

```
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user_model import User
from schemas.user_schema import UserCreate, UserOut
from db.database import get_db
from passlib.context import CryptContext
from datetime import datetime

user_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear un usuario
@user_router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_admin=user.is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Obtener un usuario por email
@user_router.get("/{email}", response_model=UserOut)
def get_user(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

# Actualizar último acceso
@user_router.patch("/{email}/last-login", response_model=UserOut)
def update_last_login(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

# Eliminar un usuario
@user_router.delete("/{email}")
def delete_user(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(db_user)
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

```

6. Dependencias (requirements.txt)

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
passlib[bcrypt]
pydantic[email]

```
Ejecución

    Configura tu base de datos Postgres: Cambia el valor de DATABASE_URL en db/database.py a tus credenciales reales.

    Instala las dependencias:

```
pip install -r requirements.txt

```

## Ejecuta la aplicación:


```
    uvicorn main:app --reload

    Accede a la documentación interactiva: Ve a http://127.0.0.1:8000/docs.

```

Para agregar autenticación con tokens JWT a la aplicación, puedes usar la librería python-jose para la generación y validación de tokens. Esto permitirá que los usuarios inicien sesión y obtengan un token JWT, que pueden usar para autenticarse en los endpoints protegidos.
Modificaciones necesarias

1. Actualiza los requisitos (requirements.txt):

python-jose[cryptography]

Instala la nueva dependencia:

pip install python-jose[cryptography]

2. Configuración de JWT

Crea un archivo auth.py para manejar la generación y validación de tokens.

auth/auth.py:

```
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuración de JWT
SECRET_KEY = "your_secret_key"  # Cambia esto a un valor seguro
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Generar un token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verificar y decodificar un token JWT
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

```

3. Rutas de autenticación

Agrega rutas para el inicio de sesión y la validación de usuarios autenticados.

Modifica routes/user_routes.py:

```
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from auth.auth import create_access_token, verify_token
from db.database import get_db
from models.user_model import User
from schemas.user_schema import UserOut

user_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Ruta para iniciar sesión
@user_router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# Dependencia para validar usuarios autenticados
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    email: str = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user

# Ruta protegida de ejemplo
@user_router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

```

4. Actualiza el esquema user_schema.py:

```
class Token(BaseModel):
    access_token: str
    token_type: str

Flujo de autenticación

    Inicio de sesión:
    Endpoint: POST /users/login
    Envía las credenciales en formato application/x-www-form-urlencoded. Ejemplo:

{
    "username": "user@example.com",
    "password": "password"
}

Respuesta:

{
    "access_token": "jwt_token",
    "token_type": "bearer"
}

Acceso a rutas protegidas:
Envía el token en el encabezado Authorization:

    Authorization: Bearer <token>

    Obtención del usuario autenticado:
    Endpoint: GET /users/me.

Ejemplo de uso

    Usa /users/login para autenticarte.
    Usa el token en /users/me o cualquier otra ruta protegida.

```

## Control de Acceso Seguridad

Para proteger más endpoints con JWT, puedes aplicar la dependencia get_current_user a cualquier ruta que deba estar protegida. Esto asegura que el usuario esté autenticado antes de acceder a la funcionalidad. Aquí tienes un paso a paso:

1. Protección de Endpoints

Reutiliza la dependencia get_current_user que validará el token JWT y recuperará la información del usuario actual.

Ejemplo de actualización en routes/user_routes.py:

```
from fastapi import Depends

# Actualizar el endpoint de eliminación de usuario para requerir autenticación
@user_router.delete("/{email}")
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Solo permite eliminar si el usuario autenticado es un administrador
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar usuarios")

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(db_user)
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

# Endpoint protegido para listar todos los usuarios (ejemplo)
@user_router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Solo los administradores pueden ver la lista completa
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para listar usuarios")

    return db.query(User).all()

```

2. Permitir a los Usuarios Acceder Solo a sus Datos

Puedes personalizar la lógica para que los usuarios solo puedan acceder a sus propios datos si no son administradores.

```
@user_router.get("/{email}", response_model=UserOut)
def get_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Los administradores pueden acceder a cualquier usuario
    if not current_user.is_admin and current_user.email != email:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este usuario")

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

```

3. Proteger Todos los Endpoints

Agrega la dependencia get_current_user como parámetro en los endpoints que requieran autenticación. Esto es útil para cualquier acción sensible, como actualización, eliminación o creación de datos confidenciales.

Ejemplo:

```
@user_router.patch("/{email}/last-login", response_model=UserOut)
def update_last_login(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Asegúrate de que el usuario puede modificar solo su propia información
    if not current_user.is_admin and current_user.email != email:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar esta información")

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

```

4. Añade Más Pruebas de Seguridad

Si deseas proteger aún más tu API, considera:

    Permisos basados en roles: Crea una lógica que use is_admin o roles adicionales.
    Rate limiting: Usa librerías como slowapi para limitar las solicitudes por usuario.
    Logging: Registra accesos y errores críticos para monitorear actividad sospechosa.

Resultado

Ahora puedes proteger cualquier endpoint simplemente añadiendo current_user: User = Depends(get_current_user) como parámetro. Esto:

    Valida el token JWT.
    Carga al usuario autenticado.
    Permite personalizar la lógica de acceso según el rol o las características del usuario.

Para implementar roles y permisos más detallados en tu aplicación, puedes usar un sistema de control de acceso basado en roles. Esto implica asignar roles específicos a los usuarios y definir qué acciones pueden realizar según su rol.
Plan para implementar roles y permisos

    Definir roles en el modelo de usuario.
    Amplía el modelo para incluir un campo role. Los roles pueden ser admin, editor, viewer, etc.

    Crear una lógica centralizada para verificar permisos.
    Escribe una función reutilizable que permita validar si un usuario tiene el rol necesario para acceder a un endpoint.

    Aplicar esta lógica a los endpoints protegidos.
    Usa dependencias o decoradores para verificar roles en los endpoints.

## Implementación

1. Actualizar el modelo de usuario

Modifica el modelo para agregar un campo role.

```
# models/user_model.py
from sqlalchemy import Column, String
from db.database import Base

class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")  # Define roles: admin, editor, viewer, etc.
    # Otros campos...

```

2. Actualizar el esquema de usuario

Incluye el campo role en los esquemas de entrada y salida.

```
# schemas/user_schema.py
class UserBase(BaseModel):
    email: EmailStr
    role: str  # El rol del usuario

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    pass

3. Crear una función de verificación de permisos

Crea una función para validar si un usuario tiene el rol necesario.

# auth/permissions.py
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.user_model import User
from auth.auth import get_current_user

def has_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")
        return current_user
    return role_checker

```

4. Aplicar verificación de roles en los endpoints

Usa la función has_role como dependencia en los endpoints para aplicar restricciones basadas en roles.

```
# routes/user_routes.py
from auth.permissions import has_role

@user_router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role(["admin"])),  # Solo administradores pueden listar usuarios
):
    return db.query(User).all()

@user_router.post("/", response_model=UserOut)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role(["admin", "editor"])),  # Admins y editores pueden crear usuarios
):
    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@user_router.delete("/{email}")
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_role(["admin"])),  # Solo administradores pueden eliminar usuarios
):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

```

5. Roles sugeridos y permisos

Define roles y permisos según tus necesidades. Por ejemplo:
Rol	Permisos
Admin	Crear, editar, eliminar y listar usuarios.
Editor	Crear y editar usuarios, pero no eliminarlos.
Viewer	Solo puede listar o ver información.

6. Pruebas

Asegúrate de probar los permisos implementados:

    Caso de éxito:
    Verifica que un usuario con el rol adecuado puede acceder al recurso.

    Caso de error:
    Verifica que un usuario sin los permisos adecuados recibe un error 403.

Ejemplo:

```
# Prueba caso de éxito
response = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
assert response.status_code == 200

# Prueba caso de error
response = client.get("/users/", headers={"Authorization": f"Bearer {viewer_token}"})
assert response.status_code == 403

```

Con esta implementación, ahora tienes un sistema flexible de control de acceso basado en roles. Puedes personalizar aún más los roles según tus necesidades.

```
