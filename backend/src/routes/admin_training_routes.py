from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError # Para el debug de errores
from typing import List, Optional

from src.models.training_models import Training
from src.schemas.trainig_schemas import TrainingOut, TrainingUpdate, TrainingCreate

from src.database import get_db
from src.utils import get_current_user, has_user_role

admin_training = APIRouter()

# Obtener todos los cursos (Sólo para Administradores) con opciones de ordenación y paginación
@admin_training.get("/training", response_model=List[TrainingOut], description="Obtener todos los cursos")
async def get_all_training(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    user_in: Optional[str] = Query(None, description="ID del usuario"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    fecha_finalizacion: Optional[str] = Query(None, description="Fecha de finalización en formato YYYY-MM-DD"),
    # Parámetros de ordenación y paginación
    order_by: Optional[str] = Query("user_id", description="Campo por el cual ordenar (user_id, fecha_inicio, fecha_finalizacion)"),
    order_direction: Optional[str] = Query("asc", description="Dirección de la ordenación (asc o desc)"),
    page: Optional[int] = Query(1, description="Número de página"),
    per_page: Optional[int] = Query(10, description="Número de registros por página"),
):
    """
    Obtener todos los cursos (Sólo para Administradores) con opciones de ordenación y paginación.

    Args:
        db (Session): Sesión de la base de datos proporcionada por la dependencia.
        current_user (dict): Usuario actual proporcionado por la dependencia.
        order_by (str): Campo por el cual ordenar.
        order_direction (str): Dirección de la ordenación.
        page (int): Número de página.
        per_page (int): Número de registros por página.

    Returns:
        List[TrainingOut]: Lista de cursos ordenados y paginados.

    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador o si los parámetros son inválidos.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )

    # Validar parámetros de ordenación
    valid_order_fields = ["user_id", "fecha_inicio", "fecha_finalizacion"]
    if order_by not in valid_order_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campo de ordenación inválido. Debe ser uno de {valid_order_fields}.",
        )
    if order_direction not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dirección de ordenación inválida. Debe ser 'asc' o 'desc'.",
        )

    # Determinar la dirección de ordenación
    order_func = asc if order_direction == "asc" else desc

    # Calcular el offset para la paginación
    offset = (page - 1) * per_page

    # Consultar la base de datos con ordenación y paginación
    trainings = (
        db.query(Training)
        .order_by(order_func(getattr(Training, order_by)))
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return trainings

# Obtener todos los cursos de un usuario (Sólo para Administradores) con opciones de ordenación y paginación
@admin_training.get("/{user_id}/training", response_model=List[TrainingOut], description="Obtener todos los cursos")
async def get_trainings(
    user_in: str,
    current_user: dict = Depends(get_current_user),
    order_by: str = Query("fecha_inicio", description="Campo por el que ordenar"),
    order_direction: str = Query("asc", description="Dirección de ordenación"),
    page: int = Query(1, description="Número de página"),
    per_page: int = Query(10, description="Número de elementos por página"),
) -> List[TrainingOut]:
    """
    Obtener todos los cursos de un usuario(Sólo para Administradores) con opciones de ordenación y paginación.

    Args:
        user_in (str): Identificador del usuario.
        db (Session): Sesión de la base de datos proporcionada por la dependencia.
        current_user (dict): Usuario actual proporcionado por la dependencia.
        order_by (str): Campo por el cual ordenar.
        order_direction (str): Dirección de la ordenación.
        page (int): Número de página.
        per_page (int): Número de registros por página.

    Returns:
        List[TrainingOut]: Lista de cursos ordenados y paginados.

    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador o si los parámetros son inválidos.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )

    # Validar parámetros de ordenación
    valid_order_fields = ["user_id", "fecha_inicio", "fecha_finalizacion"]
    if order_by not in valid_order_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campo de ordenación inválido. Debe ser uno de {valid_order_fields}.",
        )
    if order_direction not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dirección de ordenación inválida. Debe ser 'asc' o 'desc'.",
        )

    # Determinar la dirección de ordenación
    order_func = asc if order_direction == "asc" else desc

    # Calcular el offset para la paginación
    offset = (page - 1) * per_page

    # Consultar la base de datos con ordenación y paginación
    trainings = (
        db.query(Training)
        .order_by(order_func(getattr(Training, order_by)))
        .offset(offset)
        .limit(per_page)
        .filter(Training.user_id == user_in)
        .all()
    )

    return trainings

# Obtener un curso de un usuario (Sólo para Administradores) con opciones de ordenación y paginación
@admin_training.get("/{user_id}/training/{training_id}", response_model=TrainingOut, description="Obtener un curso de un usuario")
async def get_training_by_id(
    user_id: int,
    training_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener todos los cursos (Sólo para Administradores) con opciones de ordenación y paginación.

    Args:
        db (Session): Sesión de la base de datos proporcionada por la dependencia.
        current_user (dict): Usuario actual proporcionado por la dependencia.
        user_id (int): ID del usuario.
        training_id (int): ID del curso.
    Returns:
        TrainingOut (Dict): Cursos de un usuario.

    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador o si los parámetros son inválidos.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )

    # Obtener el curso por ID
    training = db.query(Training).filter(Training.id == training_id, Training.user_id == user_id).first()

    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado",
        )

    return training

# Eliminar curso de un usuario (Sólo para Administradores)
@admin_training.delete("/{user_id}/training/{training_id}", response_model=TrainingOut, description="Eliminar un curso")
async def delete_training(
    user_id: int,
    training_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar un curso de un usuario específico (Sólo para Administradores)

    Args:
        db (Session): Sesión de la base de datos proporcionada por la dependencia.
        current_user (dict): Usuario actual proporcionado por la dependencia.
        user_id (int): ID del usuario.
        training_id (int): ID del curso.
    Returns:
        TrainingOut (Dict): Cursos de un usuario borrado.

    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador o si los parámetros son inválidos.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )

    # Obtener el curso por ID
    training = db.query(Training).filter(Training.id == training_id, Training.user_id == user_id).first()

    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado",
        )

    # Eliminar el curso de la base de datos
    db.delete(training)
    db.commit()

    return training

# Modificar curso de un usuario (Sólo para Administradores)
@admin_training.put("/{user_id}/training/{training_id}", response_model=TrainingOut, description="Modificar un curso")
async def update_training(
    user_id: int,
    training_id: int,
    training_update: TrainingUpdate, db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Modificar un curso de un usuario específico.

    Args:
        db (Session): Sesión de la base de datos proporcionada por la dependencia.
        current_user (dict): Usuario actual proporcionado por la dependencia.
        user_id (int): ID del usuario.
        training_id (int): ID del curso.
        training_update (TrainingUpdate): Datos actualizados del curso.
    Returns:
        TrainingOut (Dict): Cursos de un usuario actualiado.

    Raises:
        HTTPException: Si el usuario no tiene permisos de administrador o si los parámetros son inválidos.
    """
    # Verificar si el usuario tiene el rol "admin"
    if not has_user_role(current_user, ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción",
        )

    # Obtener el curso por ID
    training = db.query(Training).filter(Training.id == training_id, Training.user_id == user_id).first()

    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado",
        )

    # Actualizar los campos del curso
    training.nombre_curso = training_update.nombre_curso
    training.institucion = training_update.institucion
    training.tipo_certificado = training_update.tipo_certificado
    training.nivel_estudio = training_update.nivel_estudio
    training.fecha_inicio = training_update.fecha_inicio
    training.fecha_finalizacion = training_update.fecha_finalizacion
    training.horas_duracion = training_update.horas_duracion
    training.area_conocimiento = training_update.area_conocimiento
    training.descripcion_curso = training_update.descripcion_curso
    training.calificacion_nota = training_update.calificacion_nota
    training.idioma = training_update.idioma
    training.nombre_profesor_instructor = training_update.nombre_profesor_instructor
    training.nombre_programa_estudios = training_update.nombre_programa_estudios
    training.pais = training_update.pais
    training.ciudad = training_update.ciudad
    training.estado_provincia = training_update.estado_provincia
    training.observaciones = training_update.observaciones

    # Guardar los cambios en la base de datos
    db.commit()
    db.refresh(training)

    return training
