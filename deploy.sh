#!/bin/bash

# Script de deploy para el backend RePA

# Detener y eliminar contenedores existentes
docker compose down

# Pullear ultima version del repositorio
git pull

# Construir y iniciar los nuevos contenedores
docker compose up -d --build

# Esperar a que PostgreSQL esté listo (el healthcheck se encarga)
echo "Esperando a que los servicios estén listos..."
sleep 5

# Verificar estado de los contenedores
docker compose ps

# Mostrar logs del backend
echo ""
echo "=== Logs del backend ==="
docker compose logs backend --tail 10

# Determinar si estamos en producción o desarrollo
if [ -n "$PROD" ] || [ "$1" == "prod" ]; then
  echo ""
  echo "Backend desplegado en producción"
else
  echo ""
  echo "Backend desplegado en http://localhost:8000"
  echo "Adminer disponible en http://localhost:8081"
fi
