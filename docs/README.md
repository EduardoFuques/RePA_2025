# RePA

El Registro Provincial Audiovisual, tiene como objetivo implementar una base de datos del Instituto de Artes Audiovisuales de Misiones, en la que se pueda registrar a todas aquellas personas que de una u otra manera están involucradas en la producción Audiovisual.

## Lógica de la aplicación:

La aplicación recopila información principalmente de dos tipos de entidades:
**Personas** y **Empresas**

### Relación de las entidades

```
RePA_app/
│
├── usuarios/
│   ├── persona*
│   ├── presentacion_personal
│   ├── obra_audiovisual
│   ├── capacitacion
│   ├── formacion*
│   ├── participacion_IAAVIM
│   ├── empresa*
│         ├── obra_audiovisual
│         ├── participacion_foros

```

La información es cargada en la plataforma a partir de un usuario.

El usuario será responsable de la información proporcionada: deberá registrar su información personal, las obras audiovisuales, capacitaciones, formación y su participación en IAAVIM.

De la misma manera, un usuario podrá registrar todas las empresas que haya creado y la información asociada a cada empresa, como las obras producidas, participaciones, etc.


## Estructura de la aplicación:

La API de Backend mantiene la sigueinte estructura de directorios:

```
my_app/
├── main.py
├── auth/
│   ├── auth.py
│   ├── permissions.py
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

- En el directorio **db** se encuentra el archivo de configuración de conexión a la base de datos, y es utilizado por los distintos módulos que necesitan conectarse a los datos.
- El directorio **auth** contiene las funcionalidades que permiten la gestión de tokens y la gestión de las Listas de Control de Acceso (ACL) de los usuarios.
- En el directorio **models** se encuentran definidos los modelos de datos para cada uno de los objetos, como *usuarios*, *personas*, *empresas*, etc.
- En el directorio **schemas** se encuentran definidas las **clases** que define la estructura de datos para cada uno de los objetos, y cómo se interactúa con ellos en cada caso.
- En el directorio **routes** se encuentra la lógica del sistema: se declaran las rutas para la ejecución de las funcionalidades del sistema, y la lógica de funcionamiento. Implementa también las ACL a cada una de las rutas, de acuerdo a la lógica de negocio definida.

Mediante esta estructura, es posible extender el funcionamiento de la API, incorporando en cada caso los distintos elementos para un "módulo" o función.

Para incorporar el "modulo" de empresa, se debe crear un *modelo* de datos, que será creado e insertado en la base de datos. Un *schema* que define las clases para el objeto de datos que se va a manipular (una empresa, un curso, etc.) y finalmente *routes* donde se define la lógica de negocio y restricciones propias del módulo a implementar.

### Buenas practicas FastAPI
En FastAPI, la documentación se incorpora de manera automática y elegante gracias a su integración con OpenAPI y Swagger UI. Aquí te explico cómo funciona y cómo puedes personalizarla:

**Documentación Automática con OpenAPI y Swagger UI**

FastAPI genera automáticamente documentación interactiva para tu API basada en:

* **Anotaciones de tipo:** FastAPI utiliza las anotaciones de tipo de Python para inferir los tipos de datos de tus parámetros y respuestas.
* **Descripciones de funciones:** Puedes agregar descripciones a tus funciones y parámetros para proporcionar información adicional.

**Cómo Acceder a la Documentación**

Una vez que tienes una aplicación FastAPI en ejecución, puedes acceder a la documentación en:

* `http://127.0.0.1:8000/docs`: Swagger UI, una interfaz interactiva que te permite probar tus endpoints directamente desde el navegador.
* `http://127.0.0.1:8000/redoc`: ReDoc, otra herramienta de documentación con un estilo diferente.

**Agregar Descripciones a tus Funciones y Parámetros**

Para mejorar la documentación, puedes agregar descripciones a tus funciones y parámetros:

* **Descripción de la función:** Agrega una cadena de documentación (docstring) a tu función.
* **Descripción de los parámetros:** Utiliza el parámetro `description` en los parámetros de ruta, consulta y cuerpo.
* **Descripción de los modelos Pydantic:** si utilizas modelos Pydantic, puedes agregar descripciones a los campos del modelo.

**Ejemplo**

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.get("/items/{item_id}")
def read_item(
    item_id: int = Path(description="The ID of the item to get."),
    q: str | None = Query(default=None, description="Query string for filtering items."),
):
    """
    Retrieves an item by its ID.
    """
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: Item):
    """
    Creates a new item.
    """
    return item
```

En este ejemplo:

* Se han agregado docstrings a las funciones `read_item` y `create_item`.
* Se ha agregado una descripción al parámetro `item_id` utilizando `Path(description="...")`.
* Se ha agregado una descripción al parametro opcional "q" utilizando `Query(default=None, description="...")`.
* Se ha agregado una descripción a los campos del modelo Pydantic "Item".

**Beneficios de la Documentación Automática de FastAPI**

* **Ahorro de tiempo:** No necesitas escribir documentación manualmente.
* **Documentación siempre actualizada:** La documentación se genera a partir de tu código, por lo que siempre está sincronizada.
* **Facilidad de uso:** Swagger UI y ReDoc proporcionan interfaces interactivas que facilitan la exploración y prueba de tu API.
* **Estandarización:** FastAPI utiliza OpenAPI, un estándar ampliamente adoptado para la documentación de APIs.

En resumen, FastAPI facilita la incorporación de documentación en tus funciones mediante el uso de anotaciones de tipo y descripciones. Esto permite generar documentación interactiva y actualizada automáticamente.

Cuando gestionas rutas en **FastAPI** con control de acceso por roles, es fundamental seguir buenas prácticas para la organización, seguridad y mantenimiento del código. Aquí están las mejores prácticas divididas en secciones:

---

## **1. Organización de las Rutas**
### **Separar rutas según funcionalidad y permisos**
- **Usuarios regulares**:  
  - `POST /auth/signup` → Crear usuario  
  - `POST /auth/login` → Iniciar sesión y obtener JWT  
  - `GET /users/me` → Recuperar datos del usuario autenticado  
  - `PUT /users/me` → Modificar datos del usuario autenticado  
  - `DELETE /users/me` → Borrar cuenta del usuario autenticado  

- **Administradores** (rutas protegidas por rol `admin`):  
  - `GET /admin/users/{user_id}` → Recuperar datos de cualquier usuario  
  - `PUT /admin/users/{user_id}` → Modificar datos de cualquier usuario  
  - `DELETE /admin/users/{user_id}` → Borrar cualquier usuario  

---

## **2. Control de Acceso con Dependencias**
### **Uso de JWT para Autenticación**
- Utilizar `OAuth2PasswordBearer` para manejar la autenticación con JWT.
- Crear una dependencia `get_current_user` que valide el token y retorne el usuario autenticado.

### **Roles con Dependencias**
- Implementar una función `get_current_admin` que verifique si el usuario autenticado tiene rol de `admin` antes de acceder a las rutas protegidas.

---

## **3. Implementación en FastAPI**
### **Ejemplo de Control de Acceso por Roles en Rutas**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List
from jose import JWTError, jwt
from pydantic import BaseModel

app = FastAPI()

# Simulación de base de datos de usuarios
fake_db = {
    "user1@example.com": {"id": 1, "name": "User One", "role": "user"},
    "admin@example.com": {"id": 2, "name": "Admin User", "role": "admin"},
}

# Clave secreta para firmar JWT (Ejemplo)
SECRET_KEY = "secret"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class User(BaseModel):
    id: int
    name: str
    role: str

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email not in fake_db:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        user_data = fake_db[email]
        return User(**user_data)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user

@app.post("/auth/signup")
def signup():
    return {"message": "Usuario creado"}

@app.post("/auth/login")
def login():
    return {"access_token": "example.jwt.token", "token_type": "bearer"}

@app.get("/users/me")
def get_my_data(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "role": user.role}

@app.put("/users/me")
def update_my_data(user: User = Depends(get_current_user)):
    return {"message": "Datos actualizados"}

@app.delete("/users/me")
def delete_my_account(user: User = Depends(get_current_user)):
    return {"message": "Cuenta eliminada"}

@app.get("/admin/users/{user_id}")
def get_user_admin(user_id: int, admin: User = Depends(get_current_admin)):
    return {"message": f"Datos del usuario {user_id}"}

@app.put("/admin/users/{user_id}")
def update_user_admin(user_id: int, admin: User = Depends(get_current_admin)):
    return {"message": f"Datos del usuario {user_id} actualizados"}

@app.delete("/admin/users/{user_id}")
def delete_user_admin(user_id: int, admin: User = Depends(get_current_admin)):
    return {"message": f"Usuario {user_id} eliminado"}
```

---

## **4. Buenas Prácticas Adicionales**
✅ **Modularizar las rutas**  
- Separar las rutas de usuarios y administradores en diferentes archivos usando **APIRouter**.  

✅ **Usar permisos basados en roles**  
- Implementar una solución más flexible con **roles dinámicos** en vez de condicionales fijos.

✅ **Cifrar contraseñas**  
- Utilizar `bcrypt` para cifrar las contraseñas antes de almacenarlas.

✅ **Implementar Refresh Tokens**  
- Evitar sesiones perpetuas, usar Refresh Tokens para renovar accesos.

✅ **Manejo de errores estructurado**  
- Definir excepciones personalizadas para respuestas más claras.

---
