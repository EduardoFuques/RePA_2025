"""
Funciones helper reutilizables para operaciones CRUD.

Reduce código duplicado en los routers de formularios (PF, PJ, Asociación, etc.)
"""

from contextlib import contextmanager
from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Type variables para tipado genérico
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

MSG_CONFLICT = (
    "Ya existe un registro con alguno de los datos únicos proporcionados "
    "(por ejemplo DNI, CUIL o CUIT)."
)


def _commit_or_conflict(db: Session, conflict_message: str = MSG_CONFLICT) -> None:
    """
    Confirma la transacción mapeando violaciones de unicidad/integridad a un
    error 409 en lugar de propagar un 500.

    Raises:
        HTTPException 409 si se viola una constraint de la base de datos.
    """
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflict_message
        )


def get_user_record(
    db: Session,
    model: type[ModelType],
    user_id: str,
    not_found_message: str = "Registro no encontrado",
) -> ModelType:
    """
    Obtiene el registro de un modelo filtrado por user_id.

    Args:
        db: Sesión de base de datos
        model: Clase del modelo SQLAlchemy
        user_id: ID del usuario actual
        not_found_message: Mensaje de error si no se encuentra

    Returns:
        Instancia del modelo encontrado

    Raises:
        HTTPException 404 si no se encuentra el registro
    """
    record = db.query(model).filter(model.user_id == user_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message
        )
    return record


def check_duplicate_record(
    db: Session,
    model: type[ModelType],
    user_id: str,
    error_message: str = "El usuario ya tiene un registro",
) -> None:
    """
    Verifica que el usuario no tenga ya un registro del modelo.

    Raises:
        HTTPException 400 si ya existe un registro
    """
    existing = db.query(model).filter(model.user_id == user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
        )


@contextmanager
def integrity_as_conflict(db: Session, conflict_message: str = MSG_CONFLICT):
    """
    Context manager: cualquier `db.flush()` (o `db.commit()`) que ocurra
    dentro del bloque y viole una constraint de unicidad/integridad se
    mapea a 409 en vez de propagar un 500. Pensado para envolver los
    `db.flush()` intermedios de `lifecycle_service.procesar_actualizacion`
    (que corren ANTES del commit final) — sin esto, un DNI/CUIT duplicado
    detectado ahí escapa como IntegrityError crudo.
    """
    try:
        yield
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflict_message
        )


def apply_update_fields(record: ModelType, data: UpdateSchemaType) -> dict:
    """
    Aplica vía setattr los campos presentes en `data` sobre `record`, SIN
    commitear. Devuelve el dict aplicado para que el caller pueda
    inspeccionarlo antes de guardar (p. ej. detectar una transición de
    ``borrador`` a enviado y disparar `lifecycle_service.procesar_actualizacion`)
    y decidir side-effects adicionales antes de `commit_or_conflict`.

    Se expone aparte (y no como un update completo) para los
    modelos registrables (PF/PJ/AS/ESA/AGAM) que necesitan ese hook.
    """
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    return update_data


def commit_or_conflict(db: Session, conflict_message: str = MSG_CONFLICT) -> None:
    """Versión pública de `_commit_or_conflict`, para callers que aplican
    lógica extra entre `apply_update_fields` y el commit."""
    _commit_or_conflict(db, conflict_message)


def create_registrable_record(
    db: Session,
    model: type[ModelType],
    data: CreateSchemaType,
    user_id: str,
    on_flush=None,
    **extra_fields,
) -> ModelType:
    """
    Crea el registro del usuario: hace `flush` antes de commitear y, si se pasa
    `on_flush(record, data_dict)`, le da la chance de reaccionar — pensado
    para `lifecycle_service.procesar_actualizacion`, por si un
    registro se crea directamente con `borrador: false` (sin pasar antes por
    un PUT de borrador), caso poco común pero posible (clientes que no usan
    el flujo multi-paso del frontend, o el propio create con default False).

    Sin `on_flush`, es un alta común (add + commit, 409 si choca un único).
    """
    db_record = model(**data.model_dump(), user_id=user_id, **extra_fields)
    db.add(db_record)
    with integrity_as_conflict(db):
        db.flush()
        if on_flush:
            on_flush(db_record, data.model_dump())
    _commit_or_conflict(db)
    db.refresh(db_record)
    return db_record


def delete_record(db: Session, record: ModelType) -> None:
    """
    Elimina un registro de la base de datos.

    Args:
        db: Sesión de base de datos
        record: Instancia del modelo a eliminar
    """
    db.delete(record)
    db.commit()


def get_record_by_id(
    db: Session,
    model: type[ModelType],
    record_id: int,
    user_id: str,
    not_found_message: str = "Registro no encontrado",
) -> ModelType:
    """
    Obtiene un registro por ID verificando que pertenezca al usuario.

    Args:
        db: Sesión de base de datos
        model: Clase del modelo SQLAlchemy
        record_id: ID del registro
        user_id: ID del usuario actual
        not_found_message: Mensaje de error si no se encuentra

    Returns:
        Instancia del modelo encontrado

    Raises:
        HTTPException 404 si no se encuentra el registro
    """
    record = (
        db.query(model).filter(model.id == record_id, model.user_id == user_id).first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message
        )
    return record
