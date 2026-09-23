# Contribuyendo al Proyecto

¡Gracias por interesarte en contribuir a nuestro proyecto! A continuación, encontrarás las pautas y políticas para contribuir de manera efectiva.

## Cómo Empezar

1. **Forkea el Repositorio**: Haz un fork del repositorio en tu cuenta de GitHub.
2. **Clona el Repositorio**: Clona el repositorio forkeado a tu máquina local.
    ```bash
    git clone https://github.com/tu-usuario/nombre-del-repositorio.git
    ```
3. **Crea una Rama**: Crea una nueva rama para tu contribución.
    ```bash
    git checkout -b nombre-de-tu-rama
    ```
3.1 **Nombre de la rama**
Para permitir una gestión ordenada de las colaboraciones, se ha estipulado de qué forma se debe nombrar una *Rama*.
El formato requerido es:
    ```bash
    nombre_del_contribuyente/[Tipo_Contribución]_[Módulo]
    ```

Tipo_Contribución:
* BUG
* FEATURE
* DOCS

Módulo:
* Es el nombre del módulo en el que se trabaja.

## Haciendo Cambios

Los cambios deben ser "pequeños", y siempre deben estar relacionados a un issue particular. Manteniendo la congruencia de que cada "commit" que se realiza debe afectar sólamente elementos estrechamente relacionados y no producir grandes cambios.

En el proyecto se establecen tres (3) tipos de colaboraciones. 

1. **Ship**
Aquellas cambios que no implican un riesgo en el código, que pueda afectar el sistema, generalmente cambios en elementos de documentación son denomonados *Ship* y pueden ser *mergeados* directamente a *main* sin la necesidad de que que se involucre terceras personas en el pull request (PR).

2. **Show**
Aquellos cambios que involucran código de la aplicación, que tienen un riesgo muy bajo de que pueden afectar el sistema, se denominan *Show*. Éstos cambios deben ser enviados a un *pull request* y revisados antes de integrarlos a la rama *main*. Si bien el desarrollador está solicitando comentarios, nada impide cuando se puede realizar el *merge*.

3. **Ask**
Aquellos cambios que involucran código de la aplicación, y que pueden afectar la funcionalidad del sistema, se denominan *Ask*. Éstos cambios deben ser enviados a un *pull request* y antes de ser aplicados a la rama *main* deben ser discutidos y evaluados por los pares. El desarrollador que envía el *pull request* debe también asegurarse de iniciar la consulta sobre el código con los pares. También sera el encargado de realizar el *merge* del código a la rama *main*-
 

1. **Realiza Cambios**: Realiza los cambios necesarios en tu rama.
2. **Pruebas**: Asegúrate de que todos los tests pasen correctamente.
3. **Commits**: Haz commits de tus cambios con mensajes claros y descriptivos.
    ```bash
    git commit -m "Descripción de los cambios"
    ```

## Enviando tu Contribución

1. **Push**: Haz push de tu rama a tu repositorio forkeado.
    ```bash
    git push origin nombre-de-tu-rama
    ```
2. **Pull Request**: Abre un pull request en el repositorio original.

## Código de Conducta

Por favor, lee nuestro [Código de Conducta](./CODE_OF_CONDUCT.md) para entender las expectativas de comportamiento en nuestra comunidad.

## Contacto

Si tienes alguna pregunta o necesitas ayuda, no dudes en abrir un issue o contactar a los mantenedores del proyecto.

¡Gracias por tu contribución!
