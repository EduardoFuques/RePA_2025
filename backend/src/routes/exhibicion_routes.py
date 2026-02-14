"""
Rutas para el registro de espacios de exhibición audiovisual.

Incluye:
- **Salas**: Espacios físicos de proyección
- **Exhibiciones**: Eventos de exhibición audiovisual
- **Festivales**: Festivales de cine y audiovisual
- **Cinematecas**: Archivos y espacios de preservación audiovisual
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.exhibicion_model import Cinemateca, Exhibicion, Festival, Sala
from src.schemas.exhibicion_schemas import (
    CinematecaCreate,
    CinematecaOut,
    CinematecaUpdate,
    ExhibicionCreate,
    ExhibicionOut,
    ExhibicionUpdate,
    FestivalCreate,
    FestivalOut,
    FestivalUpdate,
    SalaCreate,
    SalaOut,
    SalaUpdate,
)
from src.utils import get_current_user

exhibicion_router = APIRouter()


# === SALAS ===


@exhibicion_router.post(
    "/salas", response_model=SalaOut, status_code=status.HTTP_201_CREATED
)
async def create_sala(
    data: SalaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear una nueva Sala de Exhibición"""
    db_sala = Sala(**data.model_dump(), user_id=current_user["id"])
    db.add(db_sala)
    db.commit()
    db.refresh(db_sala)
    return db_sala


@exhibicion_router.get("/salas", response_model=list[SalaOut])
async def list_salas(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todas las salas del usuario"""
    return db.query(Sala).filter(Sala.user_id == current_user["id"]).all()


@exhibicion_router.get("/salas/{sala_id}", response_model=SalaOut)
async def get_sala(
    sala_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener una Sala por ID"""
    sala = (
        db.query(Sala)
        .filter(Sala.id == sala_id, Sala.user_id == current_user["id"])
        .first()
    )
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada"
        )
    return sala


@exhibicion_router.put("/salas/{sala_id}", response_model=SalaOut)
async def update_sala(
    sala_id: int,
    data: SalaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar una Sala"""
    sala = (
        db.query(Sala)
        .filter(Sala.id == sala_id, Sala.user_id == current_user["id"])
        .first()
    )
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sala, key, value)

    db.commit()
    db.refresh(sala)
    return sala


@exhibicion_router.delete("/salas/{sala_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sala(
    sala_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una Sala"""
    sala = (
        db.query(Sala)
        .filter(Sala.id == sala_id, Sala.user_id == current_user["id"])
        .first()
    )
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada"
        )

    db.delete(sala)
    db.commit()
    return None


# === EXHIBICIONES ===


@exhibicion_router.post(
    "/", response_model=ExhibicionOut, status_code=status.HTTP_201_CREATED
)
async def create_exhibicion(
    data: ExhibicionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear una nueva Exhibición"""
    db_exhibicion = Exhibicion(**data.model_dump(), user_id=current_user["id"])
    db.add(db_exhibicion)
    db.commit()
    db.refresh(db_exhibicion)
    return db_exhibicion


@exhibicion_router.get("/", response_model=list[ExhibicionOut])
async def list_exhibiciones(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todas las exhibiciones del usuario"""
    return db.query(Exhibicion).filter(Exhibicion.user_id == current_user["id"]).all()


@exhibicion_router.get("/me", response_model=ExhibicionOut)
async def get_my_exhibicion(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener la Exhibición del usuario actual"""
    exhibicion = (
        db.query(Exhibicion).filter(Exhibicion.user_id == current_user["id"]).first()
    )
    if not exhibicion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró exhibición para este usuario",
        )
    return exhibicion


@exhibicion_router.get("/{exhibicion_id}", response_model=ExhibicionOut)
async def get_exhibicion(
    exhibicion_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener una Exhibición por ID"""
    exhibicion = (
        db.query(Exhibicion)
        .filter(
            Exhibicion.id == exhibicion_id, Exhibicion.user_id == current_user["id"]
        )
        .first()
    )
    if not exhibicion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibición no encontrada"
        )
    return exhibicion


@exhibicion_router.put("/{exhibicion_id}", response_model=ExhibicionOut)
async def update_exhibicion(
    exhibicion_id: int,
    data: ExhibicionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar una Exhibición"""
    exhibicion = (
        db.query(Exhibicion)
        .filter(
            Exhibicion.id == exhibicion_id, Exhibicion.user_id == current_user["id"]
        )
        .first()
    )
    if not exhibicion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibición no encontrada"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exhibicion, key, value)

    db.commit()
    db.refresh(exhibicion)
    return exhibicion


@exhibicion_router.delete("/{exhibicion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exhibicion(
    exhibicion_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una Exhibición"""
    exhibicion = (
        db.query(Exhibicion)
        .filter(
            Exhibicion.id == exhibicion_id, Exhibicion.user_id == current_user["id"]
        )
        .first()
    )
    if not exhibicion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibición no encontrada"
        )

    db.delete(exhibicion)
    db.commit()
    return None


# === FESTIVALES ===


@exhibicion_router.post(
    "/festivales", response_model=FestivalOut, status_code=status.HTTP_201_CREATED
)
async def create_festival(
    data: FestivalCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un nuevo Festival"""
    db_festival = Festival(**data.model_dump(), user_id=current_user["id"])
    db.add(db_festival)
    db.commit()
    db.refresh(db_festival)
    return db_festival


@exhibicion_router.get("/festivales", response_model=list[FestivalOut])
async def list_festivales(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los festivales del usuario"""
    return db.query(Festival).filter(Festival.user_id == current_user["id"]).all()


@exhibicion_router.get("/festivales/{festival_id}", response_model=FestivalOut)
async def get_festival(
    festival_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Festival por ID"""
    festival = (
        db.query(Festival)
        .filter(Festival.id == festival_id, Festival.user_id == current_user["id"])
        .first()
    )
    if not festival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Festival no encontrado"
        )
    return festival


@exhibicion_router.put("/festivales/{festival_id}", response_model=FestivalOut)
async def update_festival(
    festival_id: int,
    data: FestivalUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Festival"""
    festival = (
        db.query(Festival)
        .filter(Festival.id == festival_id, Festival.user_id == current_user["id"])
        .first()
    )
    if not festival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Festival no encontrado"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(festival, key, value)

    db.commit()
    db.refresh(festival)
    return festival


@exhibicion_router.delete(
    "/festivales/{festival_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_festival(
    festival_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Festival"""
    festival = (
        db.query(Festival)
        .filter(Festival.id == festival_id, Festival.user_id == current_user["id"])
        .first()
    )
    if not festival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Festival no encontrado"
        )

    db.delete(festival)
    db.commit()
    return None


# === CINEMATECA ===


@exhibicion_router.post(
    "/cinemateca", response_model=CinematecaOut, status_code=status.HTTP_201_CREATED
)
async def create_cinemateca(
    data: CinematecaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un registro de Cinemateca para una obra"""
    db_cinemateca = Cinemateca(**data.model_dump())
    db.add(db_cinemateca)
    db.commit()
    db.refresh(db_cinemateca)
    return db_cinemateca


@exhibicion_router.get("/cinemateca", response_model=list[CinematecaOut])
async def list_cinemateca(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los registros de Cinemateca"""
    return db.query(Cinemateca).all()


@exhibicion_router.get("/cinemateca/{cinemateca_id}", response_model=CinematecaOut)
async def get_cinemateca(
    cinemateca_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un registro de Cinemateca por ID"""
    cinemateca = db.query(Cinemateca).filter(Cinemateca.id == cinemateca_id).first()
    if not cinemateca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )
    return cinemateca


@exhibicion_router.put("/cinemateca/{cinemateca_id}", response_model=CinematecaOut)
async def update_cinemateca(
    cinemateca_id: int,
    data: CinematecaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un registro de Cinemateca"""
    cinemateca = db.query(Cinemateca).filter(Cinemateca.id == cinemateca_id).first()
    if not cinemateca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cinemateca, key, value)

    db.commit()
    db.refresh(cinemateca)
    return cinemateca


@exhibicion_router.delete(
    "/cinemateca/{cinemateca_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_cinemateca(
    cinemateca_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un registro de Cinemateca"""
    cinemateca = db.query(Cinemateca).filter(Cinemateca.id == cinemateca_id).first()
    if not cinemateca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )

    db.delete(cinemateca)
    db.commit()
    return None
