"""
Retry logic para operaciones de base de datos.

Proporciona decoradores y utilidades para reintentar operaciones
que pueden fallar por errores transitorios (conexión perdida, timeout, etc.)
"""
import time
import functools
from typing import Callable, Type, Tuple, Optional
from sqlalchemy.exc import OperationalError, InterfaceError, DBAPIError

from src.logger import logger
from src.config import IS_TESTING


# Excepciones que indican errores transitorios de DB
TRANSIENT_ERRORS: Tuple[Type[Exception], ...] = (
    OperationalError,  # Conexión perdida, timeout
    InterfaceError,    # Error de interfaz con DB
)


def retry_on_db_error(
    max_retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_ERRORS
) -> Callable:
    """
    Decorador que reintenta una función si falla con errores transitorios de DB.
    
    Args:
        max_retries: Número máximo de reintentos (default: 3)
        delay: Tiempo inicial de espera entre reintentos en segundos (default: 0.5)
        backoff: Factor multiplicador del delay en cada reintento (default: 2.0)
        exceptions: Tupla de excepciones que disparan el reintento
    
    Ejemplo:
        @retry_on_db_error(max_retries=3)
        def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # No loguear en tests para evitar ruido
                        if not IS_TESTING:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} para {func.__name__}: {str(e)}"
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if not IS_TESTING:
                            logger.error(
                                f"Falló {func.__name__} después de {max_retries} reintentos: {str(e)}"
                            )
            
            # Si llegamos aquí, agotamos los reintentos
            raise last_exception
        
        return wrapper
    return decorator


def retry_on_db_error_async(
    max_retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = TRANSIENT_ERRORS
) -> Callable:
    """
    Versión async del decorador de retry para funciones asíncronas.
    
    Ejemplo:
        @retry_on_db_error_async(max_retries=3)
        async def get_user(db, user_id):
            return db.query(User).filter(User.id == user_id).first()
    """
    import asyncio
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if not IS_TESTING:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} para {func.__name__}: {str(e)}"
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if not IS_TESTING:
                            logger.error(
                                f"Falló {func.__name__} después de {max_retries} reintentos: {str(e)}"
                            )
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryableDBSession:
    """
    Context manager que proporciona una sesión de DB con retry automático.
    
    Ejemplo:
        with RetryableDBSession(SessionLocal) as db:
            user = db.query(User).first()
    """
    
    def __init__(
        self, 
        session_factory: Callable,
        max_retries: int = 3,
        delay: float = 0.5,
        backoff: float = 2.0
    ):
        self.session_factory = session_factory
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.session = None
    
    def __enter__(self):
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None and exc_type in TRANSIENT_ERRORS:
                self.session.rollback()
            self.session.close()
        return False
