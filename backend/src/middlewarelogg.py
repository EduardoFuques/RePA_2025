import re
import time
import uuid
from contextvars import ContextVar

import jwt
from fastapi import Request

from src.config import ALGORITHM, SECRET_KEY
from src.logger import logger

# Identificador de la request en curso. Vive en un ContextVar para que cualquier
# capa (auditoría, servicios) pueda anotarlo sin recibir el Request por
# parámetro: así una fila de audit_logs se puede correlacionar con su línea de
# log, y de ahí con todo lo que pasó en esa misma request.
request_id_actual: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """request_id de la request en curso, o None fuera de una request."""
    return request_id_actual.get()


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

    Ya no se usa en el log canónico —volcar todos los headers de cada request
    era ruido, no información— pero se mantiene para cuando haga falta loguear
    headers puntualmente durante una investigación.

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


def _identificar_usuario(request: Request) -> tuple[str | None, str]:
    """(user_id, estado_auth) a partir del Bearer token, sin tocar la base."""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None, "anonymous"

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # El id del usuario viaja en `sub` (ver create_access_token). El código
        # anterior leía `id`, una clave que el token no trae: el log siempre
        # decía usuario desconocido aunque la request estuviera autenticada.
        return payload.get("sub") or payload.get("id"), "authenticated"
    except jwt.ExpiredSignatureError:
        return None, "expired_token"
    except jwt.InvalidTokenError:
        return None, "invalid_token"


async def log_requests(request: Request, call_next):
    """
    Canonical logging: **una** línea JSON por request, emitida al SALIR.

    Antes se logueaba al entrar, con headers y query params completos pero sin
    lo único que importa para operar: status, latencia y si reventó. Y encima el
    dict se pasaba como `msg` y como `extra`, así que quedaba duplicado y
    aplanado a texto.

    Ahora cada request emite un solo evento con todo lo necesario para
    responder "¿qué pasó?" sin cruzar varias líneas, correlacionable por
    `request_id` con las filas de `audit_logs` que haya generado.
    """
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    token_ctx = request_id_actual.set(request_id)
    # `request.state` para que los endpoints también puedan leerlo.
    request.state.request_id = request_id

    user_id, estado_auth = _identificar_usuario(request)
    inicio = time.perf_counter()
    status_code = 500
    error = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
        evento = {
            "request_id": request_id,
            "method": request.method,
            "path": redactar_url(request.url.path),
            "query_params": filtrar_query_params(dict(request.query_params)),
            "status": status_code,
            "duration_ms": duracion_ms,
            "user_id": user_id,
            "auth": estado_auth,
            "client_ip": request.client.host if request.client else None,
        }
        if error:
            evento["error"] = error

        nivel = logger.error if (error or status_code >= 500) else logger.info
        nivel(
            f"{request.method} {request.url.path} {status_code} {duracion_ms}ms",
            extra=evento,
        )
        request_id_actual.reset(token_ctx)
