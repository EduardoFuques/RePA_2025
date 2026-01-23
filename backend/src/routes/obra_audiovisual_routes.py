# routes/obra_audiovisual_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.models.obra_audiovisual_model import ObraAudiovisual, EquipoTecnicoObra
from src.schemas.obra_audiovisual_schemas import (
    ObraAudiovisualCreate, ObraAudiovisualUpdate, ObraAudiovisualOut, ObraAudiovisualList,
    EquipoTecnicoCreate, EquipoTecnicoOut
)
from src.database import get_db
from src.utils import get_current_user

obra_audiovisual_router = APIRouter()


# === CRUD OBRA AUDIOVISUAL ===

@obra_audiovisual_router.post("/", response_model=ObraAudiovisualOut, status_code=status.HTTP_201_CREATED)
async def create_obra(
    data: ObraAudiovisualCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva Obra Audiovisual"""
    # Extraer equipo técnico si viene en el request
    equipo_data = data.equipo_tecnico
    obra_data = data.model_dump(exclude={'equipo_tecnico'})
    
    db_obra = ObraAudiovisual(**obra_data, user_id=current_user["id"])
    db.add(db_obra)
    db.commit()
    db.refresh(db_obra)
    
    # Agregar equipo técnico si se proporcionó
    if equipo_data:
        for miembro in equipo_data:
            equipo = EquipoTecnicoObra(**miembro.model_dump(), obra_id=db_obra.id)
            db.add(equipo)
        db.commit()
        db.refresh(db_obra)
    
    return db_obra


@obra_audiovisual_router.get("/", response_model=List[ObraAudiovisualList])
async def list_obras(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar todas las obras del usuario actual"""
    return db.query(ObraAudiovisual).filter(ObraAudiovisual.user_id == current_user["id"]).all()


@obra_audiovisual_router.get("/{obra_id}", response_model=ObraAudiovisualOut)
async def get_obra(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener una Obra Audiovisual por ID"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra no encontrada"
        )
    return obra


@obra_audiovisual_router.put("/{obra_id}", response_model=ObraAudiovisualOut)
async def update_obra(
    obra_id: int,
    data: ObraAudiovisualUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar una Obra Audiovisual"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra no encontrada"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obra, key, value)
    
    db.commit()
    db.refresh(obra)
    return obra


@obra_audiovisual_router.delete("/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_obra(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una Obra Audiovisual"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra no encontrada"
        )
    
    db.delete(obra)
    db.commit()
    return None


# === EQUIPO TÉCNICO ===

@obra_audiovisual_router.post("/{obra_id}/equipo", response_model=EquipoTecnicoOut, status_code=status.HTTP_201_CREATED)
async def add_miembro_equipo(
    obra_id: int,
    data: EquipoTecnicoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar un miembro al equipo técnico de una obra"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    
    miembro = EquipoTecnicoObra(**data.model_dump(), obra_id=obra.id)
    db.add(miembro)
    db.commit()
    db.refresh(miembro)
    return miembro


@obra_audiovisual_router.get("/{obra_id}/equipo", response_model=List[EquipoTecnicoOut])
async def get_equipo_tecnico(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el equipo técnico de una obra"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    
    return db.query(EquipoTecnicoObra).filter(EquipoTecnicoObra.obra_id == obra.id).all()


@obra_audiovisual_router.put("/{obra_id}/equipo/{miembro_id}", response_model=EquipoTecnicoOut)
async def update_miembro_equipo(
    obra_id: int,
    miembro_id: int,
    data: EquipoTecnicoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un miembro del equipo técnico"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    
    miembro = db.query(EquipoTecnicoObra).filter(
        EquipoTecnicoObra.id == miembro_id,
        EquipoTecnicoObra.obra_id == obra.id
    ).first()
    if not miembro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    
    for key, value in data.model_dump().items():
        setattr(miembro, key, value)
    
    db.commit()
    db.refresh(miembro)
    return miembro


@obra_audiovisual_router.delete("/{obra_id}/equipo/{miembro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_miembro_equipo(
    obra_id: int,
    miembro_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un miembro del equipo técnico"""
    obra = db.query(ObraAudiovisual).filter(
        ObraAudiovisual.id == obra_id,
        ObraAudiovisual.user_id == current_user["id"]
    ).first()
    if not obra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    
    miembro = db.query(EquipoTecnicoObra).filter(
        EquipoTecnicoObra.id == miembro_id,
        EquipoTecnicoObra.obra_id == obra.id
    ).first()
    if not miembro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    
    db.delete(miembro)
    db.commit()
    return None
