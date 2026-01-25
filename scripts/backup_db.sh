#!/bin/bash
# =============================================================================
# Script de backup automático para PostgreSQL - RePA 2025
# =============================================================================
# Uso: ./backup_db.sh
# Configurar en cron: 0 2 * * * /ruta/al/proyecto/scripts/backup_db.sh
# =============================================================================

set -e

# Configuración (puede sobrescribirse con variables de entorno)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/repa}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
CONTAINER_NAME="${CONTAINER_NAME:-repa_2025-db-1}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="repa_backup_${TIMESTAMP}.sql.gz"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Crear directorio de backups si no existe
mkdir -p "${BACKUP_DIR}"

log_info "Iniciando backup de base de datos RePA..."
log_info "Directorio de backups: ${BACKUP_DIR}"
log_info "Retención: ${RETENTION_DAYS} días"

# Verificar que el contenedor está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_error "El contenedor ${CONTAINER_NAME} no está corriendo"
    exit 1
fi

# Obtener credenciales del contenedor
POSTGRES_USER=$(docker exec ${CONTAINER_NAME} printenv POSTGRES_USER)
POSTGRES_DB=$(docker exec ${CONTAINER_NAME} printenv POSTGRES_DB)

if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
    log_error "No se pudieron obtener las credenciales de PostgreSQL"
    exit 1
fi

log_info "Base de datos: ${POSTGRES_DB}"
log_info "Usuario: ${POSTGRES_USER}"

# Realizar backup
log_info "Ejecutando pg_dump..."
if docker exec ${CONTAINER_NAME} pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    log_info "Backup creado exitosamente: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    log_error "Error al crear el backup"
    exit 1
fi

# Verificar integridad del backup (que no esté vacío)
if [ ! -s "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    log_error "El archivo de backup está vacío"
    rm -f "${BACKUP_DIR}/${BACKUP_FILE}"
    exit 1
fi

# Limpiar backups antiguos
log_info "Limpiando backups con más de ${RETENTION_DAYS} días..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "repa_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [ "$DELETED_COUNT" -gt 0 ]; then
    log_info "Se eliminaron ${DELETED_COUNT} backups antiguos"
else
    log_info "No hay backups antiguos para eliminar"
fi

# Mostrar estado actual de backups
log_info "Backups disponibles:"
ls -lh "${BACKUP_DIR}"/repa_backup_*.sql.gz 2>/dev/null | tail -10 || log_warn "No se encontraron backups"

# Calcular espacio usado
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log_info "Espacio total usado por backups: ${TOTAL_SIZE}"

log_info "Backup completado exitosamente"
