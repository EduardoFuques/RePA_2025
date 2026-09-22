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

# Lo que hay que configurar UNA VEZ

Nada de esto lo puede hacer el codigo — son credenciales y permisos.

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

## 3. Sembrar el primer tag

El repo no tenia ningun tag, y sin un punto de partida semantic-release
empieza en `1.0.0` — hacia atras respecto del `1.9.0` que ya declaraba
`.version`. Por eso hay que sembrar el tag una vez:

```bash
git tag v1.9.0 <commit de main previo a este cambio>
git push origin v1.9.0
```

Ese tag **no** dispara `docker-publish.yml` si se pushea con credenciales de
usuario normales antes de que el workflow exista en `main`; si llegara a
dispararlo, no hace daño: publica la imagen de esa version.

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

## El frontend sigue construyendose en el servidor

A proposito. Su bundle hornea las variables `VITE_*` en build-time
(`VITE_SHOW_TEST_USERS`, los datos de contacto de la landing), asi que una
sola imagen no sirve para QA y prod: publicarlo hoy obligaria a mantener un
tag por entorno, que es justo la duplicacion que este cambio viene a sacar.

Eso queda para la **Etapa 2** (anotada en `BACKLOG.md`): que esas variables
se lean en runtime desde el contenedor. Recien ahi el servidor deja de
construir nada.

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

## El repositorio del frontend no es accesible con la cuenta actual

`git@github.com:EduardoFuques/Repa2025-Frontend.git` responde *"Repository
not found"* por SSH y 404 por API con la cuenta `edu6565`. Hoy no bloquea
nada, porque el frontend se construye en el servidor con el submodulo que ya
esta clonado ahi. **Pero bloquea la Etapa 2**: para que Actions construya el
frontend hace falta que pueda hacer checkout del submodulo, y el
`GITHUB_TOKEN` por defecto no da acceso a otro repositorio — hay que agregar
un deploy key o un PAT con acceso a ese repo.
