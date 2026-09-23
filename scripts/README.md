# Scripts de Mantenimiento - RePA 2025

## Backup de Base de Datos

### Backup Manual

```bash
cd /home/deploy/RePA_2025
./scripts/backup_db.sh
```

### Configurar Backup Automático (Cron)

Ejecutar diariamente a las 2:00 AM:

```bash
# Editar crontab
crontab -e

# Agregar esta línea:
0 2 * * * /home/deploy/RePA_2025/scripts/backup_db.sh >> /var/log/repa_backup.log 2>&1
```

### Variables de Configuración

Las variables se configuran en el archivo `.env` en la raíz del proyecto:

```env
# En .env
BACKUP_DIR=/var/backups/repa
BACKUP_RETENTION_DAYS=7
```

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BACKUP_DIR` | `/var/backups/repa` | Directorio donde se guardan los backups |
| `BACKUP_RETENTION_DAYS` | `7` | Días de retención de backups |
| `CONTAINER_NAME` | `repa_2025-db-1` | Nombre del contenedor PostgreSQL |

También se pueden sobrescribir al ejecutar:

```bash
BACKUP_DIR=/mnt/backups BACKUP_RETENTION_DAYS=14 ./scripts/backup_db.sh
```

## Restauración de Base de Datos

### Listar Backups Disponibles

```bash
ls -lh /var/backups/repa/
```

### Restaurar un Backup

```bash
./scripts/restore_db.sh /var/backups/repa/repa_backup_20260125_020000.sql.gz
```

**⚠️ ATENCIÓN**: La restauración sobrescribe TODOS los datos actuales.

## Estructura de Backups

```
/var/backups/repa/
├── repa_backup_20260125_020000.sql.gz
├── repa_backup_20260124_020000.sql.gz
├── repa_backup_20260123_020000.sql.gz
└── ...
```

Los backups más antiguos que `RETENTION_DAYS` se eliminan automáticamente.

## Verificar Logs

```bash
# Ver últimos logs de backup
tail -50 /var/log/repa_backup.log

# Ver backups existentes y espacio usado
du -sh /var/backups/repa/
ls -lh /var/backups/repa/
```
