import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from src.config import IS_TESTING, LOGS_PATH


# Atributos que `logging` pone en todo LogRecord. Cualquier otro llegó por
# `extra={...}` en la llamada, así que es contexto que queremos en el JSON.
_ATRIBUTOS_ESTANDAR = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "stacklevel", "thread", "threadName",
    "taskName",
}


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

        # Campos extra.
        #
        # Antes solo se leía `record.extra_data`, una clave que nadie seteaba
        # nunca: todo el contexto que el middleware pasaba por `extra={...}`
        # se descartaba y terminaba como repr de dict dentro de `message`.
        # Ahora se recoge cualquier atributo que no sea de los que `logging`
        # pone por su cuenta, que es exactamente lo que llegó por `extra`.
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        for clave, valor in record.__dict__.items():
            if clave not in _ATRIBUTOS_ESTANDAR and clave != "extra_data":
                log_data[clave] = valor

        return json.dumps(log_data, ensure_ascii=False, default=str)


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
            delay=True,  # delay=True para no crear archivo hasta el primer log
        )
        file_handler.setFormatter(JSONFormatter())
        handlers.append(file_handler)
    except (PermissionError, OSError):
        # Si no hay permisos, solo usar consola
        pass

# Configurar el logger raíz
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), handlers=handlers)

# Obtener el logger principal
logger = logging.getLogger("repa")
logger.setLevel(getattr(logging, log_level, logging.INFO))
