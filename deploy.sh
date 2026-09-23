#!/bin/bash

# Script de deploy para RePA (backend + frontend unificado)
# El frontend actúa como proxy reverso - backend y DB no expuestos externamente

set -e

echo "=== Deploy RePA ==="
echo ""

# Un deploy a la vez. Desde que el frontend se publica y despliega desde su
# propio repositorio, a este servidor le llegan deploys de DOS workflows
# (backend y frontend) que pueden coincidir: dos `docker compose up` en
# paralelo se pisan. La `concurrency` de GitHub Actions no cruza entre
# repositorios, asi que el cerrojo va aca. El segundo espera al primero.
exec 9>"${DEPLOY_LOCK:-/tmp/repa-deploy.lock}"
if ! flock -w 900 9; then
  echo "❌ Hay otro deploy corriendo hace mas de 15 minutos; no se sigue."
  exit 1
fi

# Cargar .env para leer SSL_DOMAIN (docker compose ya lo hace solo al
# correr, pero acá lo necesitamos ANTES, para decidir qué -f pasarle).
#
# BACKEND_REGISTRY_IMAGE se guarda antes y se restaura despues: el .env del
# servidor tiene escrita la version que corre HOY, y sourcearlo pisaria la
# que pasa docker-publish.yml en el deploy — el servidor se quedaria
# desplegando eternamente la version anterior. Lo que viene del entorno
# manda; el .env es el valor por defecto.
# Lo mismo con FRONTEND_REGISTRY_IMAGE, que pasa el docker-publish.yml del
# repositorio del frontend.
BACKEND_REGISTRY_IMAGE_ENTORNO="$BACKEND_REGISTRY_IMAGE"
FRONTEND_REGISTRY_IMAGE_ENTORNO="$FRONTEND_REGISTRY_IMAGE"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
if [ -n "$BACKEND_REGISTRY_IMAGE_ENTORNO" ]; then
  BACKEND_REGISTRY_IMAGE="$BACKEND_REGISTRY_IMAGE_ENTORNO"
fi
if [ -n "$FRONTEND_REGISTRY_IMAGE_ENTORNO" ]; then
  FRONTEND_REGISTRY_IMAGE="$FRONTEND_REGISTRY_IMAGE_ENTORNO"
fi

# HTTPS es opt-in: si configuraste SSL_DOMAIN en .env, se agrega el
# override docker-compose.ssl.yml (puerto 443 + certificados montados en
# /certs; la imagen del frontend activa sola su config HTTPS). Si no,
# sigue siendo HTTP-only como siempre.
#
# A propósito NO se valida acá que el certificado exista: certbot deja
# /etc/letsencrypt/live/ en 700 root:root, así que este script (corriendo
# como usuario normal) no puede ni leer el directorio para chequearlo —
# el chequeo fallaba en silencio y el deploy quedaba HTTP-only sin avisar
# nada. Docker sí puede montarlo (el daemon corre como root), así que se
# deja que `docker compose up` sea el que falle fuerte y claro si
# SSL_DOMAIN está mal configurado o el certificado no existe.
# Que compose usar. COMPOSE_ENV=prod selecciona docker-compose.prod.yml
# (ENVIRONMENT=production, sin --reload, sin bind mount del codigo, SECRET_KEY y
# CORS_ORIGINS obligatorios, frontend sin usuarios de prueba). Cualquier otro
# valor —incluido no definirlo— usa el compose de desarrollo, que es lo que
# necesita QA para tener el seed y las pantallas de prueba.
if [ "$COMPOSE_ENV" = "prod" ] || [ "$COMPOSE_ENV" = "production" ]; then
  echo "✓ COMPOSE_ENV=$COMPOSE_ENV — usando docker-compose.prod.yml"
  COMPOSE_FILES=(-f docker-compose.prod.yml)
else
  echo "ℹ COMPOSE_ENV no es 'prod' — usando docker-compose.yml (dev/QA)"
  COMPOSE_FILES=(-f docker-compose.yml)
fi

if [ -n "$SSL_DOMAIN" ]; then
  echo "✓ SSL_DOMAIN=$SSL_DOMAIN — habilitando HTTPS"
  COMPOSE_FILES+=(-f docker-compose.ssl.yml)
else
  echo "ℹ SSL_DOMAIN no configurado — deploy HTTP-only"
fi
echo ""

# De donde sale la imagen del backend.
#
# Si BACKEND_REGISTRY_IMAGE esta definida (la setea docker-publish.yml en
# cada deploy, o vos a mano en el .env para volver a una version anterior),
# el backend se BAJA de GHCR ya construido. Si no, se construye acá como
# siempre — el modo viejo sigue funcionando para desarrollo local y como
# salida de emergencia si el registry no esta disponible.
#
# Por que importa: el build del backend en el servidor medido tardaba 11,8
# minutos, y 254 segundos de eso eran una sola capa (el apt-get). Bajar el
# manifest son segundos. Y ademas la imagen es EXACTAMENTE la que paso el
# CI, no una reconstruccion que `pip install` podria resolver a versiones
# distintas (hallazgo DEP-16 de la auditoria).
if [ -n "$BACKEND_REGISTRY_IMAGE" ]; then
  export BACKEND_IMAGE="$BACKEND_REGISTRY_IMAGE"
  USAR_REGISTRY=1
  echo "✓ Backend desde el registry: $BACKEND_IMAGE"
else
  # Sin registry el backend se construye acá, y la imagen queda con un tag
  # fijo: la version del backend la define el tag de git, no este script.
  export BACKEND_IMAGE="repa-backend:local"
  USAR_REGISTRY=0
  echo "ℹ BACKEND_REGISTRY_IMAGE no definida — el backend se construye acá"
fi

# De donde sale la imagen del frontend. Mismo esquema que el backend: la
# publica el repositorio del frontend en GHCR (una imagen para todos los
# entornos, la config se lee al arrancar) y su docker-publish.yml despliega
# pasando FRONTEND_REGISTRY_IMAGE, que queda escrita en el .env.
#
# Sin ella se construye desde ./frontend, que ya NO es un submodulo: es un
# clon suelto del repositorio del frontend, ignorado por git. Sirve para
# desarrollo local y como salida de emergencia si el registry no responde.
if [ -n "$FRONTEND_REGISTRY_IMAGE" ]; then
  export FRONTEND_IMAGE="$FRONTEND_REGISTRY_IMAGE"
  FRONTEND_DESDE_REGISTRY=1
  echo "✓ Frontend desde el registry: $FRONTEND_IMAGE"
elif [ -f frontend/Dockerfile ]; then
  export FRONTEND_IMAGE="repa-frontend:local"
  FRONTEND_DESDE_REGISTRY=0
  echo "ℹ FRONTEND_REGISTRY_IMAGE no definida — el frontend se construye desde ./frontend ($(git -C frontend rev-parse --short HEAD 2>/dev/null || echo 'sin git'))"
else
  echo "❌ No hay de donde sacar el frontend: FRONTEND_REGISTRY_IMAGE no esta"
  echo "   definida y ./frontend no tiene un checkout del repositorio."
  echo "   Definila en el .env (ver .env.example) o cloná Repa2025-Frontend en ./frontend."
  exit 1
fi
echo ""

# =============================================================================
# El orden de lo que sigue es lo que define cuanto dura el corte.
# =============================================================================
#
# ANTES ESTO EMPEZABA CON `docker compose down`, y estaba mal por dos razones
# independientes:
#
#   1. Bajaba TODO —base de datos incluida— para actualizar un solo servicio.
#      Postgres tarda ~6s en frenar y ~18s en volver a estar healthy, y no
#      habia ninguna razon para tocarlo: su imagen y su configuracion no
#      cambian en un deploy del backend.
#
#   2. Dejaba el pull de la imagen DENTRO de la ventana de corte. El pull de
#      v1.10.0 tardo 1m16s en frio: un minuto y cuarto de servicio caido
#      esperando una descarga que se podria haber hecho con todo funcionando.
#
# Ahora: primero se trae todo lo necesario con el sistema en pie (codigo,
# imagenes del backend y del frontend), y recien al final se reconcilia.
#
# LA CLAVE ES QUE `docker compose up -d` YA HACE LO QUE QUEREMOS. Es
# declarativo: compara cada contenedor corriendo contra lo que declara el
# compose y recrea UNICAMENTE aquellos cuya imagen o configuracion cambio.
# Si el backend cambio de tag, recrea el backend; la base de datos y el
# frontend ni se enteran. `down` + `up` era la forma manual —y destructiva—
# de hacer algo que compose resuelve solo.
#
# CONSECUENCIA A TENER PRESENTE: si algun dia cambia el spec de la base
# (por ejemplo un PR de Dependabot que suba postgres:17-alpine), `up -d` SI
# va a recrear ese contenedor, porque corresponde. Los datos no se pierden:
# viven en el bind mount ./pgdata, no en el contenedor.

# --- 1. Codigo. Sin corte: todavia no se toco nada que este corriendo. -----
#
# El `git pull` se saltea si el repo esta en HEAD detached, que es como lo
# deja docker-publish.yml: el workflow hace `git checkout vX.Y.Z` para que
# el codigo del servidor sea exactamente el del tag que se publico. Un
# `git pull` ahi falla ("You are not currently on a branch") y cortaba el
# deploy por `set -e`.
echo "Actualizando backend..."
if git symbolic-ref -q HEAD >/dev/null; then
  git pull
else
  echo "  HEAD detached en $(git rev-parse --short HEAD) — no se hace pull"
fi

echo ""

# --- 2. Imagenes. Sigue sin haber corte: el sistema viejo atiende igual. ---
#
# Todo lo lento va aca, a proposito: las descargas (o los builds, si no hay
# registry) pasan con la version anterior en pie y sirviendo.
if [ "$USAR_REGISTRY" = "1" ]; then
  echo "Bajando la imagen del backend..."
  if ! docker compose "${COMPOSE_FILES[@]}" pull backend; then
    echo ""
    echo "❌ No se pudo bajar $BACKEND_IMAGE"
    echo "   Si es un 401/denied: el servidor no esta logueado en GHCR."
    echo "   Ver 'docker login ghcr.io' en docs/deploy-registry.md."
    echo ""
    echo "   No se toco nada: el sistema sigue corriendo la version anterior."
    exit 1
  fi
else
  echo "Construyendo el backend..."
  docker compose "${COMPOSE_FILES[@]}" build backend
fi

if [ "$FRONTEND_DESDE_REGISTRY" = "1" ]; then
  echo "Bajando la imagen del frontend..."
  if ! docker compose "${COMPOSE_FILES[@]}" pull frontend; then
    echo ""
    echo "❌ No se pudo bajar $FRONTEND_IMAGE"
    echo "   Si es un 401/denied: el token de GHCR del servidor no puede leer"
    echo "   el paquete repa-frontend. Ver docs/deploy-registry.md."
    echo ""
    echo "   No se toco nada: el sistema sigue corriendo la version anterior."
    exit 1
  fi
else
  echo "Construyendo el frontend..."
  docker compose "${COMPOSE_FILES[@]}" build frontend
fi
echo ""

# --- 3. Escotilla de emergencia: forzar un reinicio completo. --------------
#
# El flujo normal NO baja nada. Si hiciera falta el comportamiento viejo
# —por ejemplo para descartar un estado raro de red o de volumenes— se corre
# el deploy con DEPLOY_RECREAR_TODO=1. Es deliberadamente explicito: que
# tirar la base de datos sea una decision que alguien toma y escribe, no el
# default de todos los dias.
if [ "$DEPLOY_RECREAR_TODO" = "1" ]; then
  echo "⚠ DEPLOY_RECREAR_TODO=1 — bajando TODO, base de datos incluida"
  docker compose "${COMPOSE_FILES[@]}" down --remove-orphans
  echo ""
fi

# --- 4. Base de datos: no se toca, solo se verifica que responda. ---------
#
# `up -d db` es idempotente: si ya esta corriendo y su spec no cambio, no
# hace absolutamente nada y devuelve al instante. Si esta caida, la levanta.
# Esta explicito —y no delegado al depends_on del backend— para que, cuando
# la base sea el problema, el deploy lo diga con todas las letras en vez de
# fallar mas adelante con un error de conexion.
echo "Verificando la base de datos..."
docker compose "${COMPOSE_FILES[@]}" up -d db

for i in {1..6}; do
  if docker compose "${COMPOSE_FILES[@]}" ps db | grep -q "healthy"; then
    echo "✓ PostgreSQL healthy"
    break
  fi
  if [ $i -eq 6 ]; then
    echo "❌ PostgreSQL no alcanzó estado healthy"
    docker compose "${COMPOSE_FILES[@]}" logs db --tail=20
    exit 1
  fi
  echo "  Esperando DB... ($i/6)"
  sleep 5
done
echo ""

# --- 5. Reconciliar. Acá, y solo acá, hay corte. --------------------------
#
# Dura lo que tarde en reiniciar el servicio que efectivamente cambio
# (~20s el backend), no los ~4 minutos que tardaba el ciclo completo.
#
# --remove-orphans borra los contenedores que pertenecen a este proyecto
# pero ya no estan declarados en ningun compose. Es lo que saca el
# `repa_2025-adminer-1` que alguien levanto a mano y quedo dando vueltas —
# un cliente web de base de datos suelto en un servidor con datos de padron.
# Y es lo que evita que vuelva a acumularse algo asi sin que nadie lo note.
echo "Aplicando cambios..."
docker compose "${COMPOSE_FILES[@]}" up -d --remove-orphans

# Queda escrito en el servidor que version corre. Es lo que se edita para
# volver atras: cambiar el tag acá y correr deploy.sh de nuevo.
# Vale para las dos imagenes: un deploy del frontend no toca la linea del
# backend y viceversa, asi que cada una queda con la ultima que se desplego.
guardar_en_env() {
  local clave=$1 valor=$2
  [ -f .env ] || return 0
  if grep -q "^${clave}=" .env; then
    sed -i "s|^${clave}=.*|${clave}=${valor}|" .env
  else
    printf '\n%s=%s\n' "$clave" "$valor" >> .env
  fi
}
if [ "$USAR_REGISTRY" = "1" ]; then
  guardar_en_env BACKEND_REGISTRY_IMAGE "$BACKEND_REGISTRY_IMAGE"
fi
if [ "$FRONTEND_DESDE_REGISTRY" = "1" ]; then
  guardar_en_env FRONTEND_REGISTRY_IMAGE "$FRONTEND_REGISTRY_IMAGE"
fi

# Esperar a que el Backend esté healthy (máx 60s)
echo "Esperando a que el Backend esté healthy..."
for i in {1..12}; do
  if docker compose "${COMPOSE_FILES[@]}" ps backend | grep -q "healthy"; then
    echo "✓ Backend healthy"
    break
  fi
  if [ $i -eq 12 ]; then
    echo "❌ Backend no alcanzó estado healthy"
    echo ""
    echo "=== Logs del backend ==="
    docker compose "${COMPOSE_FILES[@]}" logs backend --tail=50
    exit 1
  fi
  echo "  Esperando Backend... ($i/12)"
  sleep 5
done

# Esperar a que el Frontend esté healthy (máx 60s). La imagen trae un
# HEALTHCHECK contra /healthz, que responde nginx sin pasar por el backend.
# Se lee el estado exacto con `docker inspect` y no con grep sobre `ps`:
# "unhealthy" tambien contiene "healthy".
echo "Esperando a que el Frontend esté healthy..."
FRONTEND_ID=$(docker compose "${COMPOSE_FILES[@]}" ps -q frontend)
for i in {1..12}; do
  ESTADO_FRONTEND=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}sin-healthcheck{{end}}' "$FRONTEND_ID" 2>/dev/null || echo "no-existe")
  if [ "$ESTADO_FRONTEND" = "healthy" ] || [ "$ESTADO_FRONTEND" = "sin-healthcheck" ]; then
    echo "✓ Frontend $ESTADO_FRONTEND"
    break
  fi
  if [ $i -eq 12 ]; then
    echo "❌ Frontend no alcanzó estado healthy ($ESTADO_FRONTEND)"
    echo ""
    echo "=== Logs del frontend ==="
    docker compose "${COMPOSE_FILES[@]}" logs frontend --tail=50
    exit 1
  fi
  echo "  Esperando Frontend ($ESTADO_FRONTEND)... ($i/12)"
  sleep 5
done

# Verificar estado
echo ""
echo "=== Estado de los contenedores ==="
docker compose "${COMPOSE_FILES[@]}" ps

# Verificar que no haya contenedores en estado unhealthy o exited
if docker compose "${COMPOSE_FILES[@]}" ps | grep -E "(unhealthy|Exit)"; then
  echo ""
  echo "❌ Hay contenedores con problemas:"
  docker compose "${COMPOSE_FILES[@]}" logs --tail=30
  exit 1
fi

# Mostrar logs del backend
echo ""
echo "=== Logs del backend ==="
docker compose "${COMPOSE_FILES[@]}" logs backend --tail 10

echo ""
echo "=== Deploy completado ==="
echo "Backend:  $BACKEND_IMAGE"
if [ "$FRONTEND_DESDE_REGISTRY" = "1" ]; then
  echo "Frontend: $FRONTEND_IMAGE"
else
  echo "Frontend: $FRONTEND_IMAGE (construido acá desde ./frontend)"
fi
echo "Frontend: http://localhost (puerto 80)"
echo "API: http://localhost/api (proxy al backend)"
echo ""
echo "Backend y PostgreSQL NO están expuestos externamente."
