"""
Rutas para el formulario de Asociación/Colectivo del RePA.

Permite registrar grupos, colectivos y asociaciones audiovisuales,
incluyendo sus ámbitos de actuación e integrantes vinculados al RePA.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crud_helpers import (
    check_duplicate_record,
    create_record,
    delete_record,
    get_user_record,
    update_record,
)
from src.database import get_db
from src.models.asociacion_model import Asociacion, IntegranteAsociacion
from src.schemas.asociacion_schemas import (
    AsociacionCreate,
    AsociacionOut,
    AsociacionUpdate,
    IntegranteAsociacionCreate,
    IntegranteAsociacionOut,
)
from src.utils import get_current_user

asociacion_router = APIRouter()

# Mensajes de error reutilizables
MSG_NOT_FOUND = "No se encontró registro de Asociación/Colectivo"
MSG_DUPLICATE = "El usuario ya tiene un registro de Asociación/Colectivo"


# === CRUD ASOCIACIÓN ===


@asociacion_router.post(
    "/",
    response_model=AsociacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de Asociación/Colectivo",
    responses={
        201: {"description": "Registro creado exitosamente"},
        400: {"description": "El usuario ya tiene un registro"},
        401: {"description": "No autenticado"},
    },
)
async def create_asociacion(
    data: AsociacionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crear el registro de Asociación/Colectivo para el usuario autenticado.

    Incluye datos básicos, ámbitos de actuación (producción, formación, exhibición, etc.)
    e integrantes. Cada usuario solo puede tener **un registro** de Asociación.
    """
    check_duplicate_record(db, Asociacion, current_user["id"], MSG_DUPLICATE)
    return create_record(db, Asociacion, data, current_user["id"])


@asociacion_router.get("/me", response_model=AsociacionOut)
async def get_my_asociacion(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el registro de Asociación/Colectivo del usuario actual"""
    return get_user_record(db, Asociacion, current_user["id"], MSG_NOT_FOUND)


@asociacion_router.put("/me", response_model=AsociacionOut)
async def update_my_asociacion(
    data: AsociacionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el registro de Asociación/Colectivo del usuario actual"""
    asoc = get_user_record(db, Asociacion, current_user["id"], MSG_NOT_FOUND)
    return update_record(db, asoc, data)


@asociacion_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_asociacion(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Eliminar el registro de Asociación/Colectivo del usuario actual"""
    asoc = get_user_record(db, Asociacion, current_user["id"], MSG_NOT_FOUND)
    delete_record(db, asoc)
    return None


# === INTEGRANTES ===


@asociacion_router.post(
    "/me/integrantes",
    response_model=IntegranteAsociacionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_integrante(
    data: IntegranteAsociacionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar un integrante a la Asociación/Colectivo"""
    asoc = get_user_record(
        db, Asociacion, current_user["id"], "Asociación no encontrada"
    )

    integrante = IntegranteAsociacion(**data.model_dump(), asociacion_id=asoc.id)
    db.add(integrante)
    db.commit()
    db.refresh(integrante)
    return integrante


@asociacion_router.get("/me/integrantes", response_model=list[IntegranteAsociacionOut])
async def get_integrantes(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener integrantes de la Asociación/Colectivo"""
    asoc = get_user_record(
        db, Asociacion, current_user["id"], "Asociación no encontrada"
    )
    return (
        db.query(IntegranteAsociacion)
        .filter(IntegranteAsociacion.asociacion_id == asoc.id)
        .all()
    )


@asociacion_router.put(
    "/me/integrantes/{integrante_id}", response_model=IntegranteAsociacionOut
)
async def update_integrante(
    integrante_id: int,
    data: IntegranteAsociacionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un integrante de la Asociación/Colectivo"""
    asoc = db.query(Asociacion).filter(Asociacion.user_id == current_user["id"]).first()
    if not asoc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asociación no encontrada"
        )

    integrante = (
        db.query(IntegranteAsociacion)
        .filter(
            IntegranteAsociacion.id == integrante_id,
            IntegranteAsociacion.asociacion_id == asoc.id,
        )
        .first()
    )
    if not integrante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integrante no encontrado"
        )

    for key, value in data.model_dump().items():
        setattr(integrante, key, value)

    db.commit()
    db.refresh(integrante)
    return integrante


@asociacion_router.delete(
    "/me/integrantes/{integrante_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_integrante(
    integrante_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un integrante de la Asociación/Colectivo"""
    asoc = db.query(Asociacion).filter(Asociacion.user_id == current_user["id"]).first()
    if not asoc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asociación no encontrada"
        )

    integrante = (
        db.query(IntegranteAsociacion)
        .filter(
            IntegranteAsociacion.id == integrante_id,
            IntegranteAsociacion.asociacion_id == asoc.id,
        )
        .first()
    )
    if not integrante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integrante no encontrado"
        )

    db.delete(integrante)
    db.commit()
    return None
