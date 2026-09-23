# Deploy por imagen (GHCR) — que cambia y que hay que configurar

Hasta ahora el servidor construia la imagen del backend en cada deploy. Eso
tardaba **11,8 minutos** medidos, de los cuales 254 segundos eran una sola
capa (el `apt-get` del Dockerfile), y ademas se pagaba dos veces: el CI ya
construia la imagen para verificar que compilaba, y la tiraba.

Ahora se construye una sola vez, en GitHub Actions, se publica en GHCR y el
servidor **baja** el manifest.

## La cadena completa

```
push a main
   └─> ci.yml          tests, migraciones, lint, pip-audit, build-check
        └─> release.yml semantic-release lee los commits y, si amerita,
                        crea el tag vX.Y.Z + GitHub Release
             └─> docker-publish.yml   build + push a GHCR, mueve `latest`,
                                      y despliega QA con el tag exacto
```

Si los commits desde el ultimo tag son todos `chore:`/`ci:`/`docs:`, no hay
version nueva: no se publica imagen y **no se toca QA**. Eso es deliberado —
un merge que no cambia comportamiento no deberia mover un entorno.

## Lo que tarda, y cuanto de eso es corte

Son dos cosas distintas y conviene no confundirlas: lo que tarda el deploy
entero, y cuanto tiempo el sistema no atiende.

El orden de `deploy.sh` esta pensado para que casi nada de lo lento caiga
dentro del corte:

| Etapa | Hay corte? |
| --- | --- |
| 1. Actualizar codigo | no |
| 2. Bajar las imagenes del backend y del frontend (1m 16s en frio) | **no** |
| 3. (Solo sin registry) construirlas | **no** |
| 4. Verificar que la base responda | no (no se la toca) |
| 5. `docker compose up -d` reconcilia | **si**, ~20s |

Todo lo caro pasa con la version anterior en pie y atendiendo. El corte es
solo el paso 5, y dura lo que tarde en reiniciar el servicio que
efectivamente cambio.

**Como era antes.** El script arrancaba con `docker compose down`, asi que
bajaba todo —base de datos incluida— y recien despues bajaba la imagen: el
pull de 1m 16s ocurria con el servicio caido. El corte era practicamente el
deploy completo, unos 4 minutos, para actualizar un solo contenedor.

Y todo esto contra los **11,8 minutos** que tardaba, antes del registry,
solo el build del backend en el servidor.

## Como volver atras (rollback)

Antes: rebuildear el commit anterior en el servidor, otros ~12 minutos.

Ahora, en el servidor:

```bash
cd ~/RePA_2025
# editar la linea BACKEND_REGISTRY_IMAGE del .env y poner el tag anterior
./deploy.sh
```

Son segundos, y corre **exactamente el mismo binario** que ya habia
funcionado, no una reconstruccion que `pip install` podria resolver a
versiones distintas de las dependencias.

Los tags publicados se ven en la pestaña **Packages** del repo, o con
`docker buildx imagetools inspect ghcr.io/eduardofuques/repa-backend:latest`.

---

# Configuracion (hecha el 22/09/2026)

Nada de esto lo puede hacer el codigo — son credenciales y permisos. Queda
documentado para cuando haya que rehacerlo, o replicarlo en produccion.

> **El error que costo dos corridas.** El secret se habia cargado como
> `GHRC_USER` en vez de `GHCR_USER` (las letras cambiadas). No fallaba donde
> uno esperaria: el `docker login` era el segundo sintoma, pero el primero
> fue que el paso de SSH ni siquiera llegaba a conectarse, cortando con
> `username is empty` — una variable vacia listada en `envs:` le corrompe el
> manejo de entorno a drone-ssh, y el mensaje apunta al secret equivocado.
> Si algun dia aparece ese error, **revisar primero que todos los secrets
> listados en `envs:` existan y esten bien escritos.**

## 1. Secrets del repositorio

En *Settings > Secrets and variables > Actions*:

| Secret | Para que | Como se saca |
| --- | --- | --- |
| `RELEASE_TOKEN` | Crear el tag y disparar `docker-publish.yml`. **No sirve el `GITHUB_TOKEN` por defecto**: un tag creado con el token automatico no dispara otros workflows (proteccion anti-loop de Actions), y la cadena se corta ahi en silencio. | PAT clasico con scope `repo` + `workflow` |
| `GHCR_USER` | Usuario con el que el servidor se loguea a GHCR | el usuario de GitHub dueño del PAT de abajo |
| `GHCR_TOKEN` | Que el servidor pueda bajar la imagen | PAT clasico con scope `read:packages` **y nada mas** |

Los `QA_HOST`, `QA_USER`, `QA_SSH_KEY` y `QA_SSH_PORT` ya existian y se
siguen usando igual.

## 2. Visibilidad del paquete en GHCR

La primera publicacion crea el paquete como **privado**, aunque el repo sea
publico. Con `GHCR_TOKEN` configurado el servidor puede bajarlo igual, asi
que no hace falta cambiarlo — pero si se lo hace publico
(*Package settings > Change visibility*), el paso de `docker login` del
servidor deja de ser necesario. Decision de Eduardo; el default privado es
el mas conservador y es el que asume este setup.

## 3. Sembrar el primer tag — hecho

El repo no tenia ningun tag, y sin un punto de partida semantic-release
empieza en `1.0.0` — hacia atras respecto del `1.9.0` que ya declaraba
`.version`. Se sembro `v1.9.0` sobre el commit `15ba4c2` (el merge del PR
#22), y la primera version que salio de la cadena fue **v1.10.0**.

No hay que repetirlo. Queda anotado por si alguna vez se arranca de cero en
otro repositorio.

## 4. Login de GHCR en el servidor (persistente)

`docker-publish.yml` hace `docker login` en cada deploy, asi que el deploy
automatico funciona solo. Pero si alguien corre `./deploy.sh` **a mano** en
el servidor, necesita que el login ya este hecho:

```bash
echo "<PAT con read:packages>" | docker login ghcr.io -u <usuario> --password-stdin
```

Docker lo guarda en `~/.docker/config.json` y sobrevive reinicios. Si falta,
`deploy.sh` corta con un mensaje explicito en vez de un 401 sin contexto.

---

# Cosas que conviene saber

## El deploy no baja nada: `up -d` es declarativo

`docker compose up -d` compara lo que esta corriendo contra lo que declara el
compose y recrea **unicamente** los contenedores cuya imagen o configuracion
cambio. Si cambio el tag del backend, recrea el backend; la base de datos y
el frontend ni se enteran.

Por eso `deploy.sh` ya no hace `down`. No es una optimizacion arriesgada: es
dejar de hacer a mano —y de forma destructiva— algo que compose resuelve
solo.

Dos consecuencias que conviene tener presentes:

- **Si cambia el spec de la base** (por ejemplo un PR de Dependabot que suba
  `postgres:17-alpine`), `up -d` **si** va a recrear ese contenedor, porque
  corresponde. Los datos no se pierden: viven en el bind mount `./pgdata`,
  no en el contenedor. Pero ese deploy va a tener un corte mas largo.
- **`--remove-orphans`** borra los contenedores que pertenecen al proyecto
  pero ya no estan declarados en ningun compose. Es lo que saco el
  `repa_2025-adminer-1` que alguien habia levantado a mano, y lo que evita
  que se vuelva a acumular algo asi sin que nadie lo note. Si alguna vez hace
  falta un contenedor auxiliar, va declarado en un compose — si no, el
  proximo deploy se lo lleva.

Para forzar el comportamiento viejo (bajar todo, por ejemplo para descartar
un estado raro de red o de volumenes):

```bash
DEPLOY_RECREAR_TODO=1 ./deploy.sh
```

Es deliberadamente explicito: que tirar la base de datos sea una decision que
alguien toma y escribe, no el default de todos los dias.

## El frontend tambien sale del registry

Mismo esquema que el backend, desde su propio repositorio
(`EduardoFuques/Repa2025-Frontend`): semantic-release crea el tag, su
`docker-publish.yml` publica `ghcr.io/eduardofuques/repa-frontend:vX.Y.Z` y
despliega a QA corriendo este `deploy.sh` con `FRONTEND_REGISTRY_IMAGE`, que
queda escrita en el `.env`. Volver atras es cambiar ese tag y correr
`./deploy.sh`.

Lo que lo hizo posible (Etapa 2): la imagen es una sola para todos los
entornos. Los datos de contacto de la landing se leen al arrancar el
contenedor (`environment:` del compose, que el frontend vuelca a `/env.js`)
y los usuarios de prueba los entrega el backend (`/users/demo-accounts`,
solo con `SEED_DEMO_DATA` y nunca en produccion).

**El frontend ya no es un submodulo.** El puntero se bumpeaba a mano y se
olvidaba: hasta el 23/09 QA servia el frontend del 21/08. Ahora cada repo
despliega lo suyo, y lo que corre lo dicen `BACKEND_REGISTRY_IMAGE` y
`FRONTEND_REGISTRY_IMAGE` en el `.env` del servidor. Para desarrollo local,
el frontend se clona suelto en `./frontend` (ignorado por git); sin
`FRONTEND_REGISTRY_IMAGE`, `deploy.sh` y los compose lo construyen de ahi.

**Consecuencia: los deploys son independientes.** Si un cambio del frontend
necesita un endpoint nuevo del backend, el backend se despliega primero.
`deploy.sh` toma un `flock` para que dos deploys que coincidan (uno de cada
repo) no se pisen.

## En QA, el codigo sale del bind mount, no de la imagen

`docker-compose.yml` (el que usa QA) monta `./backend/src` sobre `/code/src`.
O sea que en QA el backend corre el codigo del **checkout del servidor**, no
el que viene adentro de la imagen; de la imagen salen las dependencias de
Python ya instaladas, que es de donde venia el grueso de los 11,8 minutos.

No es un problema mientras el workflow haga `git checkout vX.Y.Z` antes del
deploy — el codigo del checkout es el mismo que el de la imagen. Pero si
alguien toca archivos a mano en el servidor, en QA eso se ve y en produccion
no (`docker-compose.prod.yml` no tiene el bind mount). Conviene tenerlo
presente al diagnosticar una diferencia entre entornos.

