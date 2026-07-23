#!/bin/bash

# Script de deploy para RePA (backend + frontend unificado)
# El frontend actúa como proxy reverso - backend y DB no expuestos externamente

set -e

FRONTEND_REPO="git@github.com:EduardoFuques/Repa2025-Frontend.git"
FRONTEND_BRANCH="main"

echo "=== Deploy RePA ==="
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
docker compose down

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
docker compose up -d --build

# Esperar a que la DB esté healthy (máx 30s)
echo "Esperando a que PostgreSQL esté healthy..."
for i in {1..6}; do
  if docker compose ps db | grep -q "healthy"; then
    echo "✓ PostgreSQL healthy"
    break
  fi
  if [ $i -eq 6 ]; then
    echo "❌ PostgreSQL no alcanzó estado healthy"
    docker compose logs db --tail=20
    exit 1
  fi
  echo "  Esperando DB... ($i/6)"
  sleep 5
done

# Esperar a que el Backend esté healthy (máx 60s)
echo "Esperando a que el Backend esté healthy..."
for i in {1..12}; do
  if docker compose ps backend | grep -q "healthy"; then
    echo "✓ Backend healthy"
    break
  fi
  if [ $i -eq 12 ]; then
    echo "❌ Backend no alcanzó estado healthy"
    echo ""
    echo "=== Logs del backend ==="
    docker compose logs backend --tail=50
    exit 1
  fi
  echo "  Esperando Backend... ($i/12)"
  sleep 5
done

# Verificar estado
echo ""
echo "=== Estado de los contenedores ==="
docker compose ps

# Verificar que no haya contenedores en estado unhealthy o exited
if docker compose ps | grep -E "(unhealthy|Exit)"; then
  echo ""
  echo "❌ Hay contenedores con problemas:"
  docker compose logs --tail=30
  exit 1
fi

# Mostrar logs del backend
echo ""
echo "=== Logs del backend ==="
docker compose logs backend --tail 10

echo ""
echo "=== Deploy completado ==="
echo "Versiones: Backend=$BACKEND_VERSION Frontend=$FRONTEND_VERSION"
echo "Frontend: http://localhost (puerto 80)"
echo "API: http://localhost/api (proxy al backend)"
echo "Adminer: http://localhost:8081 (solo desde el servidor)"
echo ""
echo "Backend y PostgreSQL NO están expuestos externamente."
