# RePA_2025
Registro Provincial del Audiovisual

Plataforma de gestión para los recursos del Instituto de Artes Audiovisuales de Misiones

La plataforma está basada en la implementación de un API service en FastAPI, el cual consume los datos de una base de datos relacional PostgreSQL.

El backend implementa la gestión de permisos de usuario mediante roles y JSON Web Token (JWT), en un módulo inicial de CRUD de usuarios y CRUD de Roles.

## Instalación de la plataforma

Es necesario contar con docker ya instalado y funcionando correctamente.

Para instalar el entorno de desarrollo se debe ejecutar dentro del directorio del proyecto **RePA_2025** es siguiente comando:

```bash
docker compose up
```

Esto iniciará los contenedores docker con: 
* La aplicación backend en FastAPI, 
* el motor de base de datos PostgreSQL, 
* la aplicación ADMINER como interfaz web de PostgreSQL para desarrollo (En la versión de producción se elimina) y 
* la aplicación de frontend en REACT.

> [!important]
> Es importante configurar las variables de entorno en el archivo *.env* para cada servicio.
> Existen varios archivos *.env* de acuerdo a la aplicación.
> El archivo .env está alojado en el PATH `./.env` está destinado a la configuración inicial de los contenedores. En especial PostgreSQL.
> El archivo .env está alojado en el PATH `./backend/src/.env` está destinado a la configuración inicial de FastAPI y SQLAlchemist.
> El archivo .env está alojado en el PATH `./frontend/src/.env` está destinado a la configuración inicial de React.

### Variables de entorno declaradas 
| Variable                    | Valor                                          |
|-----------------------------|------------------------------------------------|
| POSTGRES_USER               | 'postgres'                                     |
| POSTGRES_PASSWORD           | 'example'                                      |
| POSTGRES_PORT               | 5432                                           |
| POSTGRES_DB                 | 'iaavim'                                       |
| POSTGRES_DBHOST             | repa2024-db-1                                  |
| DATABASE_URL                | 'postgresql://postgres:example@db:5432/iaavim' |
| SECRET_KEY                  | '09d25e094faa6cad3e7'                          |
| ALGORITHM                   | 'HS256'                                        |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30                                             |
| NODE_ENV                    | 'develop'                                      |
| PORT                        | '3000'                                         |

