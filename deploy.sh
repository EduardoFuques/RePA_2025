#!/bin/bash

# Script de deploy para RePA (backend + frontend unificado)
# El frontend actúa como proxy reverso - backend y DB no expuestos externamente

set -e

FRONTEND_REPO="git@github.com:EduardoFuques/Repa2025-Frontend.git"
FRONTEND_BRANCH="main"

echo "=== Deploy RePA ==="
echo ""

# Cargar .env para leer SSL_DOMAIN (docker compose ya lo hace solo al
# correr, pero acá lo necesitamos ANTES, para decidir qué -f pasarle).
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# HTTPS es opt-in: si SSL_DOMAIN apunta a un certificado real presente en
# este servidor, se agrega el override docker-compose.ssl.yml (puerto 443
# + nginx-ssl.conf). Si no, sigue siendo HTTP-only como siempre — no hace
# falta tocar nada en servidores sin certificado propio.
COMPOSE_FILES=(-f docker-compose.yml)
if [ -n "$SSL_DOMAIN" ] && [ -f "/etc/letsencrypt/live/$SSL_DOMAIN/fullchain.pem" ]; then
  echo "✓ Certificado encontrado para $SSL_DOMAIN — habilitando HTTPS"
  COMPOSE_FILES+=(-f docker-compose.ssl.yml)
else
  echo "ℹ Sin SSL_DOMAIN o sin certificado — deploy HTTP-only"
fi
echo ""

# Cargar versiones desde .version
if [ -f .version ]; then
  source .version
  echo "Versiones: Backend=$BACKEND_VERSION Frontend=$FRONTEND_VERSION"
else
  echo "⚠ Archivo .version no encontrado, usando 'latest'"
  export BACKEND_VERSION=latest
  export FRONTEND_VERSION=latest
fi
echo ""

# Detener contenedores existentes
echo "Deteniendo contenedores..."
docker compose "${COMPOSE_FILES[@]}" down

# Pullear ultima version del backend
echo "Actualizando backend..."
git pull

# Clonar o actualizar el frontend
echo "Actualizando frontend..."
if [ -d "frontend/.git" ]; then
  # Es un repo git clonado, actualizar
  cd frontend
  git fetch origin
  git checkout $FRONTEND_BRANCH
  git pull origin $FRONTEND_BRANCH
  cd ..
else
  # No es un repo git, eliminar y clonar
  rm -rf frontend
  git clone -b $FRONTEND_BRANCH $FRONTEND_REPO frontend
fi

# Construir y iniciar los contenedores
echo "Construyendo e iniciando contenedores..."
docker compose "${COMPOSE_FILES[@]}" up -d --build

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
echo "Versiones: Backend=$BACKEND_VERSION Frontend=$FRONTEND_VERSION"
echo "Frontend: http://localhost (puerto 80)"
echo "API: http://localhost/api (proxy al backend)"
echo "Adminer: http://localhost:8081 (solo desde el servidor)"
echo ""
echo "Backend y PostgreSQL NO están expuestos externamente."
