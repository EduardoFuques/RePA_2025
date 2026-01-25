import os
import json
import logging
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from src.config import LOGS_PATH, IS_TESTING


class JSONFormatter(logging.Formatter):
    """Formatter que genera logs en formato JSON estructurado."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar exception info si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)


# Configurar nivel desde variable de entorno
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Handler para consola (formato legible)
console_handler = logging.StreamHandler()
console_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
console_handler.setFormatter(logging.Formatter(console_format))

# Configurar handlers - solo consola por defecto, archivo si se especifica LOGS_PATH
handlers = [console_handler]

# Solo crear archivo de log si se especifica LOGS_PATH o no estamos en CI/testing
if LOGS_PATH or not IS_TESTING:
    # Usar directorio temporal si no hay permisos o estamos en CI
    if IS_TESTING:
        import tempfile
        log_directory = tempfile.gettempdir()
    else:
        log_directory = LOGS_PATH or os.path.join(os.getcwd(), "logs")
    
    try:
        os.makedirs(log_directory, exist_ok=True)
        log_file_path = os.path.join(log_directory, "app.log")
        
        file_handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
            delay=True  # delay=True para no crear archivo hasta el primer log
        )
        file_handler.setFormatter(JSONFormatter())
        handlers.append(file_handler)
    except (PermissionError, OSError):
        # Si no hay permisos, solo usar consola
        pass

# Configurar el logger raíz
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    handlers=handlers
)

# Obtener el logger principal
logger = logging.getLogger("repa")
logger.setLevel(getattr(logging, log_level, logging.INFO))
