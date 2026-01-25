"""
Módulo de Rate Limiting para protección contra ataques de fuerza bruta.

Utiliza slowapi para limitar la cantidad de solicitudes por IP en endpoints sensibles.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_client_ip(request: Request) -> str:
    """
    Obtiene la IP del cliente considerando proxies reversos.
    
    Args:
        request: Objeto Request de FastAPI.
    
    Returns:
        str: Dirección IP del cliente.
    """
    # Verificar si hay un proxy reverso (nginx)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For puede contener múltiples IPs, la primera es el cliente real
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Deshabilitar rate limiting en CI/testing
is_testing = os.getenv("CI", "false").lower() == "true" or os.getenv("TESTING", "false").lower() == "true"

# Crear instancia del limiter (deshabilitado en testing)
limiter = Limiter(key_func=get_client_ip, enabled=not is_testing)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handler personalizado para cuando se excede el límite de solicitudes.
    
    Args:
        request: Objeto Request de FastAPI.
        exc: Excepción de límite excedido.
    
    Returns:
        JSONResponse: Respuesta con código 429 Too Many Requests.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Demasiados intentos. Por favor, espere antes de intentar nuevamente.",
            "retry_after": exc.detail
        }
    )
