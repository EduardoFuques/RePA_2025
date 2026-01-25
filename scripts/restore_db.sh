#!/bin/bash
# =============================================================================
# Script de restauración de backup PostgreSQL - RePA 2025
# =============================================================================
# Uso: ./restore_db.sh <archivo_backup.sql.gz>
# Ejemplo: ./restore_db.sh /var/backups/repa/repa_backup_20260125_020000.sql.gz
# =============================================================================

set -e

# Configuración
CONTAINER_NAME="${CONTAINER_NAME:-repa_2025-db-1}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Verificar argumentos
if [ -z "$1" ]; then
    log_error "Uso: $0 <archivo_backup.sql.gz>"
    echo ""
    echo "Backups disponibles:"
    ls -lh /var/backups/repa/repa_backup_*.sql.gz 2>/dev/null || echo "No se encontraron backups en /var/backups/repa/"
    exit 1
fi

BACKUP_FILE="$1"

# Verificar que el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "El archivo de backup no existe: $BACKUP_FILE"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "El contenedor ${CONTAINER_NAME} no está corriendo"
    exit 1
fi

# Obtener credenciales
POSTGRES_USER=$(docker exec ${CONTAINER_NAME} printenv POSTGRES_USER)
POSTGRES_DB=$(docker exec ${CONTAINER_NAME} printenv POSTGRES_DB)

log_warn "⚠️  ATENCIÓN: Esto sobrescribirá TODOS los datos de la base de datos ${POSTGRES_DB}"
log_warn "Archivo a restaurar: ${BACKUP_FILE}"
echo ""
read -p "¿Está seguro de continuar? (escriba 'SI' para confirmar): " CONFIRM

if [ "$CONFIRM" != "SI" ]; then
    log_info "Restauración cancelada"
    exit 0
fi

log_info "Iniciando restauración..."

# Detener conexiones activas a la base de datos
log_info "Terminando conexiones activas..."
docker exec ${CONTAINER_NAME} psql -U "${POSTGRES_USER}" -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${POSTGRES_DB}'
AND pid <> pg_backend_pid();" 2>/dev/null || true

# Recrear la base de datos
log_info "Recreando base de datos ${POSTGRES_DB}..."
docker exec ${CONTAINER_NAME} psql -U "${POSTGRES_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"
docker exec ${CONTAINER_NAME} psql -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE ${POSTGRES_DB};"

# Restaurar backup
log_info "Restaurando datos desde ${BACKUP_FILE}..."
if gunzip -c "$BACKUP_FILE" | docker exec -i ${CONTAINER_NAME} psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; then
    log_info "✅ Restauración completada exitosamente"
else
    log_error "Error durante la restauración"
    exit 1
fi

# Verificar restauración
TABLES_COUNT=$(docker exec ${CONTAINER_NAME} psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
log_info "Tablas restauradas: ${TABLES_COUNT}"

log_info "Restauración finalizada"
