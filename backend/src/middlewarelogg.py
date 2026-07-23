import re

import jwt
from fastapi import Request

from src.config import ALGORITHM, SECRET_KEY
from src.logger import logger

# Rutas que llevan un JWT en el path: /users/confirm/{token} y
# /users/recovery/{token}. Un token de recuperación logueado en claro
# permite tomar la cuenta, así que se redacta antes de escribir el log.
_TOKEN_PATH_RE = re.compile(r"(/users/(?:confirm|recovery)/)[^/?#]+")

_PARAMS_SENSIBLES = {"token", "password", "secret", "key", "authorization"}


def redactar_url(url: str) -> str:
    """Redacta tokens embebidos en el path de la URL."""
    return _TOKEN_PATH_RE.sub(r"\1[REDACTED]", url)


def filtrar_query_params(params: dict) -> dict:
    """Redacta query params con nombres sensibles (token, password, etc.)."""
    return {
        k: "[REDACTED]" if k.lower() in _PARAMS_SENSIBLES else v
        for k, v in params.items()
    }


def filtrar_headers_sensibles(headers: dict) -> dict:
    """
    Filtra headers sensibles para no exponerlos en logs.

    Args:
        headers: Diccionario de headers HTTP.

    Returns:
        dict: Headers filtrados sin datos sensibles.
    """
    headers_sensibles = {"authorization", "cookie", "x-api-key", "x-auth-token"}
    return {
        k: "[REDACTED]" if k.lower() in headers_sensibles else v
        for k, v in headers.items()
    }


async def log_requests(request: Request, call_next):
    """
    Middleware para registrar todas las solicitudes HTTP.
    Filtra datos sensibles como tokens de autorización.

    Args:
        request: Objeto Request de FastAPI.
        call_next: Función para continuar con el siguiente middleware.

    Returns:
        Response: Respuesta del endpoint.
    """
    log_dict = {
        "method": request.method,
        "url": redactar_url(str(request.url)),
        "headers": filtrar_headers_sensibles(dict(request.headers)),
        "query_params": filtrar_query_params(dict(request.query_params)),
    }
    # Agregar condicional, si hay usuario logueado y get_current_user(request) != None
    authorization: str = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            # Decodificar el token para obtener la información del usuario
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            log_dict["user"] = (
                f"User ID: {payload.get('id')}, Email: {payload.get('email')}"
            )
        except jwt.ExpiredSignatureError:
            # Si el token ha expirado, se registra y se marca el usuario como desconocido
            logger.warning("Token expirado")
            log_dict["user"] = "Expired token"
        except jwt.InvalidTokenError as e:
            # Si ocurre un error al decodificar, se registra y se marca el usuario como desconocido
            logger.warning(f"Error decodificando token: {e}")
            log_dict["user"] = "Invalid token"
    else:
        # Si no hay token, se asume que es una solicitud de un usuario anónimo
        log_dict["user"] = "Anonymous"

    logger.info(log_dict, extra=log_dict)
    response = await call_next(request)
    return response
