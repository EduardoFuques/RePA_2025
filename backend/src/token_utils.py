from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException, status

from src.config import ACCESS_TOKEN_EXPIRE, ALGORITHM, REFRESH_TOKEN_EXPIRE, SECRET_KEY


def _decode(token: str, expected_type: str | None = None) -> dict:
    """
    Decodifica y valida un JWT.

    Args:
        token (str): Token JWT.
        expected_type (str | None): Si se indica, valida que el claim "type"
            del token coincida (ej. "access", "refresh", "recover", "verify").
    Returns:
        dict: Payload decodificado.
    Raises:
        HTTPException 401: token expirado, inválido o de tipo incorrecto.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if expected_type is not None and payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def decode_access_token(token: str) -> dict:
    """Decodifica un token de ACCESO, validando que sea de tipo "access".

    Antes no forzaba el tipo, con lo cual un refresh token (7 días) o un
    token de verificación/recuperación (24h) servía para autenticar
    cualquier endpoint protegido. Cada tipo de token tiene ahora su decoder.
    """
    return _decode(token, expected_type="access")


def decode_refresh_token(token: str) -> dict:
    """Decodifica un token de refresco, validando que sea de tipo "refresh"."""
    return _decode(token, expected_type="refresh")


def decode_verify_token(token: str) -> dict:
    """Decodifica un token de verificación de email (tipo "verify")."""
    return _decode(token, expected_type="verify")


def decode_recovery_token(token: str) -> dict:
    """Decodifica un token de recuperación de contraseña (tipo "recover")."""
    return _decode(token, expected_type="recover")


# Generar un token de acceso
def create_access_token(
    data: dict,
    expires_delta: int = None,
    type: str = "access",
    description="Generar un token JWT con los datos del usuario y una fecha de expiración opcional.",
):
    """
    Genera un access token con expiración corta.
    Args:
        data (dict): Datos del usuario a codificar en el token.
        expires_delta (int): Tiempo de expiración del token.
        type (str): Tipo de Token a generar (access, refresh o recover).
    Return:
        El token JWT codificado.
    """
    to_encode = data.copy()
    if not expires_delta:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    else:
        expires_delta = timedelta(minutes=expires_delta)
    # ACCESS_TOKEN_EXPIRE y REFRESH_TOKEN_EXPIRE provienen de la configuración

    expire = datetime.now(timezone.utc) + (expires_delta)
    # Se añade el tipo de token para distinguirlo en el refresh endpoint
    to_encode.update({"exp": expire, "type": type, "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict, description="Generar un refresh token con expiración larga."
):
    """
    Genera un refresh token con expiración larga.
    Args:
        data (dict): Datos del usuario a codificar en el token.
    Return:
        El token JWT codificado.
    """
    to_encode = data.copy()
    # REFRESH_TOKEN_EXPIRE está expresado en minutos en la configuración
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
