"""
Funciones helper reutilizables para operaciones CRUD.

Reduce código duplicado en los routers de formularios (PF, PJ, Asociación, etc.)
"""
from typing import TypeVar, Type, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel

# Type variables para tipado genérico
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def get_user_record(
    db: Session,
    model: Type[ModelType],
    user_id: str,
    not_found_message: str = "Registro no encontrado"
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_message
        )
    return record


def get_user_record_or_none(
    db: Session,
    model: Type[ModelType],
    user_id: str
) -> Optional[ModelType]:
    """
    Obtiene el registro de un modelo filtrado por user_id, o None si no existe.
    """
    return db.query(model).filter(model.user_id == user_id).first()


def check_duplicate_record(
    db: Session,
    model: Type[ModelType],
    user_id: str,
    error_message: str = "El usuario ya tiene un registro"
) -> None:
    """
    Verifica que el usuario no tenga ya un registro del modelo.
    
    Raises:
        HTTPException 400 si ya existe un registro
    """
    existing = db.query(model).filter(model.user_id == user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )


def create_record(
    db: Session,
    model: Type[ModelType],
    data: CreateSchemaType,
    user_id: str,
    **extra_fields
) -> ModelType:
    """
    Crea un nuevo registro en la base de datos.
    
    Args:
        db: Sesión de base de datos
        model: Clase del modelo SQLAlchemy
        data: Schema Pydantic con los datos
        user_id: ID del usuario actual
        **extra_fields: Campos adicionales a agregar
    
    Returns:
        Instancia del modelo creado
    """
    db_record = model(**data.model_dump(), user_id=user_id, **extra_fields)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def update_record(
    db: Session,
    record: ModelType,
    data: UpdateSchemaType
) -> ModelType:
    """
    Actualiza un registro existente con los datos proporcionados.
    
    Args:
        db: Sesión de base de datos
        record: Instancia del modelo a actualizar
        data: Schema Pydantic con los datos a actualizar
    
    Returns:
        Instancia del modelo actualizado
    """
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    return record


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
    model: Type[ModelType],
    record_id: int,
    user_id: str,
    not_found_message: str = "Registro no encontrado"
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
    record = db.query(model).filter(
        model.id == record_id,
        model.user_id == user_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_message
        )
    return record


def add_child_record(
    db: Session,
    parent_model: Type[ModelType],
    child_model: Type[Any],
    parent_id_field: str,
    data: CreateSchemaType,
    user_id: str,
    parent_not_found_message: str = "Registro padre no encontrado"
) -> Any:
    """
    Agrega un registro hijo a un registro padre.
    
    Ejemplo: Agregar integrante a Persona Jurídica
    
    Args:
        db: Sesión de base de datos
        parent_model: Modelo del registro padre
        child_model: Modelo del registro hijo
        parent_id_field: Nombre del campo FK en el hijo (ej: "persona_juridica_id")
        data: Schema con los datos del hijo
        user_id: ID del usuario actual
        parent_not_found_message: Mensaje si no se encuentra el padre
    
    Returns:
        Instancia del modelo hijo creado
    """
    # Obtener el registro padre
    parent = db.query(parent_model).filter(parent_model.user_id == user_id).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=parent_not_found_message
        )
    
    # Crear el registro hijo
    child_data = data.model_dump()
    child_data[parent_id_field] = parent.id
    
    child_record = child_model(**child_data)
    db.add(child_record)
    db.commit()
    db.refresh(child_record)
    return child_record
