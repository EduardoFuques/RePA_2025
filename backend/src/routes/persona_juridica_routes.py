"""
Rutas para el formulario de Persona Jurídica del RePA.

Permite registrar empresas, productoras, cooperativas y otras entidades
del sector audiovisual, incluyendo sus integrantes vinculados al RePA.
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
from src.models.persona_juridica_model import IntegrantePJ, PersonaJuridica
from src.schemas.persona_juridica_schemas import (
    IntegrantePJCreate,
    IntegrantePJOut,
    PersonaJuridicaCreate,
    PersonaJuridicaOut,
    PersonaJuridicaUpdate,
)
from src.utils import get_current_user

persona_juridica_router = APIRouter()

# Mensajes de error reutilizables
MSG_NOT_FOUND = "No se encontró registro de Persona Jurídica"
MSG_DUPLICATE = "El usuario ya tiene un registro de Persona Jurídica"


# === CRUD PERSONA JURÍDICA ===


@persona_juridica_router.post(
    "/",
    response_model=PersonaJuridicaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de Persona Jurídica",
    responses={
        201: {"description": "Registro creado exitosamente"},
        400: {"description": "El usuario ya tiene un registro"},
        401: {"description": "No autenticado"},
    },
)
async def create_persona_juridica(
    data: PersonaJuridicaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crear el registro de Persona Jurídica para el usuario autenticado.

    Incluye datos institucionales, representación legal, actividades audiovisuales
    y documentación. Cada usuario solo puede tener **un registro** de Persona Jurídica.
    """
    check_duplicate_record(db, PersonaJuridica, current_user["id"], MSG_DUPLICATE)
    return create_record(db, PersonaJuridica, data, current_user["id"])


@persona_juridica_router.get("/me", response_model=PersonaJuridicaOut)
async def get_my_persona_juridica(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el registro de Persona Jurídica del usuario actual"""
    return get_user_record(db, PersonaJuridica, current_user["id"], MSG_NOT_FOUND)


@persona_juridica_router.put("/me", response_model=PersonaJuridicaOut)
async def update_my_persona_juridica(
    data: PersonaJuridicaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el registro de Persona Jurídica del usuario actual"""
    pj = get_user_record(db, PersonaJuridica, current_user["id"], MSG_NOT_FOUND)
    return update_record(db, pj, data)


@persona_juridica_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_persona_juridica(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Eliminar el registro de Persona Jurídica del usuario actual"""
    pj = get_user_record(db, PersonaJuridica, current_user["id"], MSG_NOT_FOUND)
    delete_record(db, pj)
    return None


# === INTEGRANTES ===


@persona_juridica_router.post(
    "/me/integrantes",
    response_model=IntegrantePJOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_integrante(
    data: IntegrantePJCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar un integrante a la Persona Jurídica"""
    pj = get_user_record(
        db, PersonaJuridica, current_user["id"], "Persona Jurídica no encontrada"
    )

    integrante = IntegrantePJ(**data.model_dump(), persona_juridica_id=pj.id)
    db.add(integrante)
    db.commit()
    db.refresh(integrante)
    return integrante


@persona_juridica_router.get("/me/integrantes", response_model=list[IntegrantePJOut])
async def get_integrantes(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener integrantes de la Persona Jurídica"""
    pj = get_user_record(
        db, PersonaJuridica, current_user["id"], "Persona Jurídica no encontrada"
    )
    return (
        db.query(IntegrantePJ).filter(IntegrantePJ.persona_juridica_id == pj.id).all()
    )


@persona_juridica_router.put(
    "/me/integrantes/{integrante_id}", response_model=IntegrantePJOut
)
async def update_integrante(
    integrante_id: int,
    data: IntegrantePJCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un integrante de la Persona Jurídica"""
    pj = (
        db.query(PersonaJuridica)
        .filter(PersonaJuridica.user_id == current_user["id"])
        .first()
    )
    if not pj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona Jurídica no encontrada",
        )

    integrante = (
        db.query(IntegrantePJ)
        .filter(
            IntegrantePJ.id == integrante_id, IntegrantePJ.persona_juridica_id == pj.id
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


@persona_juridica_router.delete(
    "/me/integrantes/{integrante_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_integrante(
    integrante_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un integrante de la Persona Jurídica"""
    pj = (
        db.query(PersonaJuridica)
        .filter(PersonaJuridica.user_id == current_user["id"])
        .first()
    )
    if not pj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona Jurídica no encontrada",
        )

    integrante = (
        db.query(IntegrantePJ)
        .filter(
            IntegrantePJ.id == integrante_id, IntegrantePJ.persona_juridica_id == pj.id
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
