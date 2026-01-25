import os
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler

load_dotenv()


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


# Crear el directorio de logs si no existe (usar ruta relativa al directorio actual)
base_dir = os.path.dirname(os.path.abspath(__file__))
log_directory = os.getenv("LOGS_PATH", os.path.join(base_dir, "logs"))
os.makedirs(log_directory, exist_ok=True)

# Configurar el archivo de log
log_file_path = os.path.join(log_directory, "app.log")

# Configurar handler rotativo para archivo (JSON)
file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    delay=False
)
file_handler.setFormatter(JSONFormatter())

# Handler para consola (formato legible)
console_handler = logging.StreamHandler()
console_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
console_handler.setFormatter(logging.Formatter(console_format))

# Configurar nivel desde variable de entorno
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Configurar el logger raíz
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    handlers=[file_handler, console_handler]
)

# Obtener el logger principal
logger = logging.getLogger("repa")
logger.setLevel(getattr(logging, log_level, logging.INFO))
