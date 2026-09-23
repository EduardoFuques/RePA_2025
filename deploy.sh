#!/bin/bash

# Script de deploy para RePA (backend + frontend unificado)
# El frontend actúa como proxy reverso - backend y DB no expuestos externamente

set -e

echo "=== Deploy RePA ==="
echo ""

# Cargar .env para leer SSL_DOMAIN (docker compose ya lo hace solo al
# correr, pero acá lo necesitamos ANTES, para decidir qué -f pasarle).
#
# BACKEND_REGISTRY_IMAGE se guarda antes y se restaura despues: el .env del
# servidor tiene escrita la version que corre HOY, y sourcearlo pisaria la
# que pasa docker-publish.yml en el deploy — el servidor se quedaria
# desplegando eternamente la version anterior. Lo que viene del entorno
# manda; el .env es el valor por defecto.
BACKEND_REGISTRY_IMAGE_ENTORNO="$BACKEND_REGISTRY_IMAGE"
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
if [ -n "$BACKEND_REGISTRY_IMAGE_ENTORNO" ]; then
  BACKEND_REGISTRY_IMAGE="$BACKEND_REGISTRY_IMAGE_ENTORNO"
fi

# HTTPS es opt-in: si configuraste SSL_DOMAIN en .env, se agrega el
# override docker-compose.ssl.yml (puerto 443 + nginx-ssl.conf). Si no,
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

# Cargar versiones desde .version
#
# El `export` no es decorativo. `source .version` a secas deja las variables
# como variables de shell, y docker compose —que es otro proceso— no las ve:
# `image: repa-frontend:${FRONTEND_VERSION:-latest}` caia siempre al default
# y CADA deploy pisaba `repa-frontend:latest`, sin forma de saber despues que
# version de frontend estaba corriendo. Se veia en el log del deploy de
# v1.10.0: `naming to docker.io/library/repa-frontend:latest` mientras el
# resumen de este mismo script anunciaba 1.14.2.
if [ -f .version ]; then
  source .version
  export BACKEND_VERSION FRONTEND_VERSION
  echo "Versiones: Backend=$BACKEND_VERSION Frontend=$FRONTEND_VERSION"
else
  echo "⚠ Archivo .version no encontrado, usando 'latest'"
  export BACKEND_VERSION=latest
  export FRONTEND_VERSION=latest
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
  export BACKEND_IMAGE="repa-backend:${BACKEND_VERSION:-latest}"
  USAR_REGISTRY=0
  echo "ℹ BACKEND_REGISTRY_IMAGE no definida — el backend se construye acá"
fi
echo ""

# Detener contenedores existentes
echo "Deteniendo contenedores..."
docker compose "${COMPOSE_FILES[@]}" down

# Pullear ultima version del backend.
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

# Actualizar el frontend al commit pineado en el submodulo.
#
# Antes esto clonaba el repo a mano y hacia `git pull origin main`, con lo cual
# el puntero del submodulo se ignoraba y se desplegaba siempre el HEAD de main:
# backend y frontend nunca salian de forma atomica, y `git status` reportaba el
# submodulo como modificado de forma permanente.
#
# Ahora manda el puntero. Consecuencia practica del cambio: mergear algo en el
# frontend YA NO ALCANZA para que llegue al servidor — hay que bumpear el
# puntero en este repo (git add frontend && commit), que es justamente lo que
# vuelve reproducible un despliegue.
echo "Actualizando frontend (submodulo)..."
git submodule sync --recursive
if ! git submodule update --init --recursive; then
  # Primera corrida despues de declarar el submodulo: frontend/ todavia es el
  # clon suelto que dejaba el deploy anterior y git no lo reconoce como
  # submodulo registrado. Se rehace desde cero — no hay nada local que perder,
  # es un checkout de un repo remoto (el flujo viejo tambien hacia rm -rf aca).
  echo "  frontend/ no era un submodulo valido; rehaciendo el checkout"
  rm -rf frontend
  git submodule update --init --recursive
fi
echo "  frontend en: $(git -C frontend rev-parse --short HEAD)"

# Construir y/o bajar las imagenes, y levantar.
#
# Ojo con el `up` sin `--build`: compose solo construye un servicio si la
# imagen que declara su `image:` NO esta presente localmente. Por eso los
# dos pasos de abajo (pull del backend, build del frontend) alcanzan — al
# llegar al `up`, ambas imagenes ya existen y compose las usa tal cual.
if [ "$USAR_REGISTRY" = "1" ]; then
  echo "Bajando la imagen del backend..."
  if ! docker compose "${COMPOSE_FILES[@]}" pull backend; then
    echo ""
    echo "❌ No se pudo bajar $BACKEND_IMAGE"
    echo "   Si es un 401/denied: el servidor no esta logueado en GHCR."
    echo "   Ver 'docker login ghcr.io' en docs/deploy-registry.md."
    exit 1
  fi

  # El frontend todavia se construye acá: su bundle hornea las variables
  # VITE_* en build-time, asi que una sola imagen no sirve para QA y prod
  # (Etapa 2, anotada en BACKLOG.md).
  echo "Construyendo el frontend..."
  docker compose "${COMPOSE_FILES[@]}" build frontend

  echo "Iniciando contenedores..."
  docker compose "${COMPOSE_FILES[@]}" up -d

  # Queda escrito en el servidor que version corre. Es lo que se edita para
  # volver atras: cambiar el tag acá y correr deploy.sh de nuevo.
  if [ -f .env ]; then
    if grep -q '^BACKEND_REGISTRY_IMAGE=' .env; then
      sed -i "s|^BACKEND_REGISTRY_IMAGE=.*|BACKEND_REGISTRY_IMAGE=${BACKEND_REGISTRY_IMAGE}|" .env
    else
      printf '\nBACKEND_REGISTRY_IMAGE=%s\n' "$BACKEND_REGISTRY_IMAGE" >> .env
    fi
  fi
else
  echo "Construyendo e iniciando contenedores..."
  docker compose "${COMPOSE_FILES[@]}" up -d --build
fi

# Esperar a que la DB esté healthy (máx 30s)
echo "Esperando a que PostgreSQL esté healthy..."
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
echo "Frontend: repa-frontend:${FRONTEND_VERSION:-latest} (construido acá)"
echo "Frontend: http://localhost (puerto 80)"
echo "API: http://localhost/api (proxy al backend)"
echo ""
echo "Backend y PostgreSQL NO están expuestos externamente."
