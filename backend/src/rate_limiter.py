"""
Módulo de Rate Limiting para protección contra ataques de fuerza bruta.

Utiliza slowapi para limitar la cantidad de solicitudes por IP en endpoints sensibles.
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import RATE_LIMIT_ENABLED

# IPs de proxies reversos confiables (ej: nginx interno en Docker).
# Configurar vía variable de entorno TRUSTED_PROXY_IPS (separadas por coma).
_TRUSTED_PROXIES = {
    ip.strip()
    for ip in os.getenv("TRUSTED_PROXY_IPS", "172.0.0.0/8,127.0.0.1").split(",")
    if ip.strip()
}


def _is_trusted_proxy(ip: str) -> bool:
    """Verifica si una IP pertenece al rango de proxies confiables."""
    import ipaddress

    try:
        addr = ipaddress.ip_address(ip)
        for entry in _TRUSTED_PROXIES:
            try:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                if ip == entry:
                    return True
    except ValueError:
        pass
    return False


def get_client_ip(request: Request) -> str:
    """
    Obtiene la IP del cliente considerando proxies reversos confiables.
    Solo se confía en X-Forwarded-For si la request proviene de un proxy conocido,
    para evitar que un cliente externo falsifique su IP y eluda el rate limiting.

    Args:
        request: Objeto Request de FastAPI.

    Returns:
        str: Dirección IP del cliente.
    """
    remote_ip = get_remote_address(request)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded and _is_trusted_proxy(remote_ip):
        # X-Forwarded-For puede contener múltiples IPs, la primera es el cliente real
        return forwarded.split(",")[0].strip()
    return remote_ip


# Crear instancia del limiter.
# Controlado por RATE_LIMIT_ENABLED (ver config.py), cuyo default sigue siendo
# "solo en produccion": en desarrollo y testing se desactiva para no interferir
# con flujos automatizados (p.ej. E2E con multiples workers que repiten logins).
# Tenerlo como variable propia permite encenderlo en un QA expuesto a internet
# sin tener que cambiarle el ENVIRONMENT.
limiter = Limiter(key_func=get_client_ip, enabled=RATE_LIMIT_ENABLED)


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
            "retry_after": exc.detail,
        },
    )
