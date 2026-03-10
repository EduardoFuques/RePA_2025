# routes/fomento_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.fomento_model import Evaluador, TramiteFomento
from src.schemas.fomento_schemas import (
    EvaluadorCreate,
    EvaluadorOut,
    EvaluadorUpdate,
    TramiteFomentoCreate,
    TramiteFomentoOut,
    TramiteFomentoUpdate,
)
from src.utils import get_current_user

fomento_router = APIRouter(prefix="/fomento", tags=["fomento"])


# === TRÁMITE DE FOMENTO ===


@fomento_router.post(
    "/tramites",
    response_model=TramiteFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_tramite(
    data: TramiteFomentoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un nuevo Trámite de Fomento"""
    db_tramite = TramiteFomento(**data.model_dump(), user_id=current_user["id"])
    db.add(db_tramite)
    db.commit()
    db.refresh(db_tramite)
    return db_tramite


@fomento_router.get("/tramites/me", response_model=TramiteFomentoOut)
async def get_my_tramite(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el Trámite de Fomento del usuario actual"""
    tramite = (
        db.query(TramiteFomento)
        .filter(TramiteFomento.user_id == current_user["id"])
        .first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró trámite de fomento para este usuario",
        )
    return tramite


@fomento_router.put("/tramites/me", response_model=TramiteFomentoOut)
async def update_my_tramite(
    data: TramiteFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el Trámite de Fomento del usuario actual"""
    tramite = (
        db.query(TramiteFomento)
        .filter(TramiteFomento.user_id == current_user["id"])
        .first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró trámite de fomento para este usuario",
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tramite, key, value)

    db.commit()
    db.refresh(tramite)
    return tramite


@fomento_router.get("/tramites", response_model=list[TramiteFomentoOut])
async def list_tramites(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los Trámites de Fomento del usuario"""
    return (
        db.query(TramiteFomento)
        .filter(TramiteFomento.user_id == current_user["id"])
        .all()
    )


@fomento_router.get("/tramites/{tramite_id}", response_model=TramiteFomentoOut)
async def get_tramite(
    tramite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Trámite de Fomento por ID"""
    tramite = (
        db.query(TramiteFomento)
        .filter(
            TramiteFomento.id == tramite_id,
            TramiteFomento.user_id == current_user["id"],
        )
        .first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )
    return tramite


@fomento_router.put("/tramites/{tramite_id}", response_model=TramiteFomentoOut)
async def update_tramite(
    tramite_id: int,
    data: TramiteFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Trámite de Fomento"""
    tramite = (
        db.query(TramiteFomento)
        .filter(
            TramiteFomento.id == tramite_id,
            TramiteFomento.user_id == current_user["id"],
        )
        .first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tramite, key, value)

    db.commit()
    db.refresh(tramite)
    return tramite


@fomento_router.delete("/tramites/{tramite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tramite(
    tramite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Trámite de Fomento"""
    tramite = (
        db.query(TramiteFomento)
        .filter(
            TramiteFomento.id == tramite_id,
            TramiteFomento.user_id == current_user["id"],
        )
        .first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )

    db.delete(tramite)
    db.commit()
    return None


# === EVALUADOR ===


@fomento_router.post(
    "/evaluadores",
    response_model=EvaluadorOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluador(
    data: EvaluadorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un nuevo Evaluador"""
    db_evaluador = Evaluador(**data.model_dump(), user_id=current_user["id"])
    db.add(db_evaluador)
    db.commit()
    db.refresh(db_evaluador)
    return db_evaluador


@fomento_router.get("/evaluadores/me", response_model=EvaluadorOut)
async def get_my_evaluador(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el Evaluador del usuario actual"""
    evaluador = (
        db.query(Evaluador).filter(Evaluador.user_id == current_user["id"]).first()
    )
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró evaluador para este usuario",
        )
    return evaluador


@fomento_router.put("/evaluadores/me", response_model=EvaluadorOut)
async def update_my_evaluador(
    data: EvaluadorUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el Evaluador del usuario actual"""
    evaluador = (
        db.query(Evaluador).filter(Evaluador.user_id == current_user["id"]).first()
    )
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró evaluador para este usuario",
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(evaluador, key, value)

    db.commit()
    db.refresh(evaluador)
    return evaluador


@fomento_router.get("/evaluadores", response_model=list[EvaluadorOut])
async def list_evaluadores(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los Evaluadores del usuario"""
    return db.query(Evaluador).filter(Evaluador.user_id == current_user["id"]).all()


@fomento_router.get("/evaluadores/{evaluador_id}", response_model=EvaluadorOut)
async def get_evaluador(
    evaluador_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Evaluador por ID"""
    evaluador = (
        db.query(Evaluador)
        .filter(
            Evaluador.id == evaluador_id,
            Evaluador.user_id == current_user["id"],
        )
        .first()
    )
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluador no encontrado"
        )
    return evaluador


@fomento_router.put("/evaluadores/{evaluador_id}", response_model=EvaluadorOut)
async def update_evaluador(
    evaluador_id: int,
    data: EvaluadorUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Evaluador"""
    evaluador = (
        db.query(Evaluador)
        .filter(
            Evaluador.id == evaluador_id,
            Evaluador.user_id == current_user["id"],
        )
        .first()
    )
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluador no encontrado"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(evaluador, key, value)

    db.commit()
    db.refresh(evaluador)
    return evaluador


@fomento_router.delete(
    "/evaluadores/{evaluador_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_evaluador(
    evaluador_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Evaluador"""
    evaluador = (
        db.query(Evaluador)
        .filter(
            Evaluador.id == evaluador_id,
            Evaluador.user_id == current_user["id"],
        )
        .first()
    )
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluador no encontrado"
        )

    db.delete(evaluador)
    db.commit()
    return None
