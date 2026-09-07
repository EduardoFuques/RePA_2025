#!/bin/bash
# =============================================================================
# Script de backup automático para PostgreSQL - RePA 2025
# =============================================================================
# Uso: ./backup_db.sh
# Configurar en cron: 0 2 * * * /ruta/al/proyecto/scripts/backup_db.sh
# Las variables se leen desde el archivo .env en la raíz del proyecto
# =============================================================================

set -e

# Obtener el directorio del script y la raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cargar variables desde .env si existe
ENV_FILE="${PROJECT_ROOT}/.env"
if [ -f "$ENV_FILE" ]; then
    # `export $(grep ... | xargs)` se rompe en silencio con cualquier valor que
    # tenga espacios, comillas o un # —justo lo que aparece en una contraseña—
    # y deja variables mal cargadas sin avisar. `set -a` + `source` respeta el
    # contenido tal cual está escrito.
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

# Configuración (usa valores del .env o defaults)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/repa}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
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

# ---------------------------------------------------------------------------
# Backup de los adjuntos
# ---------------------------------------------------------------------------
# La base sola no alcanza: guarda las RUTAS de los documentos, no los
# documentos. Sin esto, perder el volumen deja el padrón lleno de referencias
# a archivos que ya no existen, y son justamente los respaldatorios (DNI,
# estatutos, actas) que el circuito de aprobación necesita.
UPLOADS_FILE="repa_uploads_${TIMESTAMP}.tar.gz"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-repa_2025-backend-1}"

if docker ps --format '{{.Names}}' | grep -q "^${BACKEND_CONTAINER}$"; then
    log_info "Ejecutando backup de adjuntos (${BACKEND_CONTAINER}:/app/uploads)..."
    if docker exec "${BACKEND_CONTAINER}" tar -czf - -C /app uploads \
        > "${BACKUP_DIR}/${UPLOADS_FILE}"; then
        UPLOADS_SIZE=$(du -h "${BACKUP_DIR}/${UPLOADS_FILE}" | cut -f1)
        log_info "Adjuntos respaldados: ${UPLOADS_FILE} (${UPLOADS_SIZE})"
    else
        log_error "Error al respaldar los adjuntos"
        exit 1
    fi

    if [ ! -s "${BACKUP_DIR}/${UPLOADS_FILE}" ]; then
        log_error "El backup de adjuntos está vacío"
        rm -f "${BACKUP_DIR}/${UPLOADS_FILE}"
        exit 1
    fi
else
    log_warn "El contenedor ${BACKEND_CONTAINER} no está corriendo: los adjuntos NO se respaldaron"
fi

# Limpiar backups de adjuntos antiguos, con la misma retención que la base
find "${BACKUP_DIR}" -name "repa_uploads_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Mostrar estado actual de backups
log_info "Backups disponibles:"
ls -lh "${BACKUP_DIR}"/repa_backup_*.sql.gz 2>/dev/null | tail -5 || log_warn "No se encontraron backups de base"
ls -lh "${BACKUP_DIR}"/repa_uploads_*.tar.gz 2>/dev/null | tail -5 || log_warn "No se encontraron backups de adjuntos"

# Calcular espacio usado
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log_info "Espacio total usado por backups: ${TOTAL_SIZE}"

log_info "Backup completado exitosamente"

# Los backups quedan en el MISMO host que la aplicación: perder el servidor es
# perder la base, los adjuntos y las copias, todo junto. Falta una copia fuera
# del servidor, que es una decisión de infraestructura (a dónde, con qué
# credenciales) y no se asume acá.
if [ -z "${BACKUP_REMOTE_TARGET}" ]; then
    log_warn "BACKUP_REMOTE_TARGET no está configurado: las copias quedan solo en este host."
    log_warn "Ante una pérdida del servidor se pierden también los backups."
fi
