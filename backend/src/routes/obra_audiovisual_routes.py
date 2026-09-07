# routes/obra_audiovisual_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.crud_helpers import (
    apply_update_fields,
    commit_or_conflict,
    delete_record,
    get_record_by_id,
    integrity_as_conflict,
)
from src.database import get_db
from src.models.obra_audiovisual_model import EquipoTecnicoObra, ObraAudiovisual
from src.models.persona_fisica_model import PersonaFisica
from src.schemas.obra_audiovisual_schemas import (
    EquipoTecnicoCreate,
    EquipoTecnicoOut,
    ObraAudiovisualCreate,
    ObraAudiovisualList,
    ObraAudiovisualOut,
    ObraAudiovisualUpdate,
)
from src.services import lifecycle_service
from src.utils import get_current_user, require_pf_aprobado

obra_audiovisual_router = APIRouter()

# Mensajes de error reutilizables
MSG_OBRA_NOT_FOUND = "Obra no encontrada"


def _get_obra(db: Session, obra_id: int, user_id: str) -> ObraAudiovisual:
    """Helper para obtener obra verificando pertenencia al usuario"""
    return get_record_by_id(db, ObraAudiovisual, obra_id, user_id, MSG_OBRA_NOT_FOUND)


def _titular_lookup(db: Session, user_id: str):
    """Callable perezoso para lifecycle_service: busca la PersonaFisica del
    usuario solo si de verdad se necesita (envío real, no cada request)."""
    return lambda: (
        db.query(PersonaFisica).filter(PersonaFisica.user_id == user_id).first()
    )


# === CRUD OBRA AUDIOVISUAL ===


@obra_audiovisual_router.post(
    "/", response_model=ObraAudiovisualOut, status_code=status.HTTP_201_CREATED
)
async def create_obra(
    data: ObraAudiovisualCreate,
    current_user: dict = Depends(get_current_user),
    _gate: dict = Depends(require_pf_aprobado),
    db: Session = Depends(get_db),
):
    """Crear una nueva Obra Audiovisual"""
    equipo_data = data.equipo_tecnico
    obra_data = data.model_dump(exclude={"equipo_tecnico"})

    db_obra = ObraAudiovisual(**obra_data, user_id=current_user["id"])
    db.add(db_obra)
    with integrity_as_conflict(db):
        db.flush()
        lifecycle_service.procesar_actualizacion(
            db,
            db_obra,
            obra_data,
            get_persona_fisica_titular=_titular_lookup(db, current_user["id"]),
        )
    commit_or_conflict(db)
    db.refresh(db_obra)

    if equipo_data:
        for miembro in equipo_data:
            equipo = EquipoTecnicoObra(**miembro.model_dump(), obra_id=db_obra.id)
            db.add(equipo)
        db.commit()
        db.refresh(db_obra)

    return db_obra


@obra_audiovisual_router.get("/me", response_model=ObraAudiovisualOut)
async def get_my_obra(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener la primera Obra Audiovisual del usuario actual (para formulario single-record)"""
    obra = (
        db.query(ObraAudiovisual)
        .filter(ObraAudiovisual.user_id == current_user["id"])
        .first()
    )
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró obra audiovisual para este usuario",
        )
    return obra


@obra_audiovisual_router.put("/me", response_model=ObraAudiovisualOut)
async def update_my_obra(
    data: ObraAudiovisualUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar la primera Obra Audiovisual del usuario actual.

    Al enviar el formulario (borrador: false por primera vez), AGAM no emite
    código propio — hereda como "código de trámite" el codigo_repa de la
    Persona Física del usuario (ver lifecycle_service)."""
    obra = (
        db.query(ObraAudiovisual)
        .filter(ObraAudiovisual.user_id == current_user["id"])
        .first()
    )
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró obra audiovisual para este usuario",
        )

    update_data = apply_update_fields(obra, data)
    with integrity_as_conflict(db):
        lifecycle_service.procesar_actualizacion(
            db,
            obra,
            update_data,
            get_persona_fisica_titular=_titular_lookup(db, current_user["id"]),
        )
    commit_or_conflict(db)
    db.refresh(obra)
    return obra


@obra_audiovisual_router.get("/", response_model=list[ObraAudiovisualList])
async def list_obras(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todas las obras del usuario actual"""
    return (
        db.query(ObraAudiovisual)
        .filter(ObraAudiovisual.user_id == current_user["id"])
        .all()
    )


@obra_audiovisual_router.get("/search", response_model=list[ObraAudiovisualList])
async def search_obras(
    q: str = "",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Buscar obras AGAM por título (todas las obras no-borrador del sistema)"""
    query = db.query(ObraAudiovisual).filter(ObraAudiovisual.borrador == False)  # noqa: E712
    if q.strip():
        query = query.filter(ObraAudiovisual.titulo.ilike(f"%{q.strip()}%"))
    return query.order_by(ObraAudiovisual.titulo).limit(20).all()


@obra_audiovisual_router.get("/{obra_id}", response_model=ObraAudiovisualOut)
async def get_obra(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener una Obra Audiovisual por ID"""
    return _get_obra(db, obra_id, current_user["id"])


@obra_audiovisual_router.put("/{obra_id}", response_model=ObraAudiovisualOut)
async def update_obra(
    obra_id: int,
    data: ObraAudiovisualUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar una Obra Audiovisual (ver update_my_obra para el detalle
    de emisión de código de trámite)."""
    obra = _get_obra(db, obra_id, current_user["id"])
    update_data = apply_update_fields(obra, data)
    with integrity_as_conflict(db):
        lifecycle_service.procesar_actualizacion(
            db,
            obra,
            update_data,
            get_persona_fisica_titular=_titular_lookup(db, current_user["id"]),
        )
    commit_or_conflict(db)
    db.refresh(obra)
    return obra


@obra_audiovisual_router.delete("/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_obra(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una Obra Audiovisual"""
    obra = _get_obra(db, obra_id, current_user["id"])
    delete_record(db, obra)
    return None


# === EQUIPO TÉCNICO ===


@obra_audiovisual_router.post(
    "/{obra_id}/equipo",
    response_model=EquipoTecnicoOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_miembro_equipo(
    obra_id: int,
    data: EquipoTecnicoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar un miembro al equipo técnico de una obra"""
    obra = _get_obra(db, obra_id, current_user["id"])

    miembro = EquipoTecnicoObra(**data.model_dump(), obra_id=obra.id)
    db.add(miembro)
    db.commit()
    db.refresh(miembro)
    return miembro


@obra_audiovisual_router.get("/{obra_id}/equipo", response_model=list[EquipoTecnicoOut])
async def get_equipo_tecnico(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener el equipo técnico de una obra"""
    obra = _get_obra(db, obra_id, current_user["id"])
    return (
        db.query(EquipoTecnicoObra).filter(EquipoTecnicoObra.obra_id == obra.id).all()
    )


@obra_audiovisual_router.put(
    "/{obra_id}/equipo/{miembro_id}", response_model=EquipoTecnicoOut
)
async def update_miembro_equipo(
    obra_id: int,
    miembro_id: int,
    data: EquipoTecnicoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un miembro del equipo técnico"""
    obra = (
        db.query(ObraAudiovisual)
        .filter(
            ObraAudiovisual.id == obra_id, ObraAudiovisual.user_id == current_user["id"]
        )
        .first()
    )
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada"
        )

    miembro = (
        db.query(EquipoTecnicoObra)
        .filter(
            EquipoTecnicoObra.id == miembro_id, EquipoTecnicoObra.obra_id == obra.id
        )
        .first()
    )
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado"
        )

    for key, value in data.model_dump().items():
        setattr(miembro, key, value)

    db.commit()
    db.refresh(miembro)
    return miembro


@obra_audiovisual_router.delete(
    "/{obra_id}/equipo/{miembro_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_miembro_equipo(
    obra_id: int,
    miembro_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un miembro del equipo técnico"""
    obra = (
        db.query(ObraAudiovisual)
        .filter(
            ObraAudiovisual.id == obra_id, ObraAudiovisual.user_id == current_user["id"]
        )
        .first()
    )
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada"
        )

    miembro = (
        db.query(EquipoTecnicoObra)
        .filter(
            EquipoTecnicoObra.id == miembro_id, EquipoTecnicoObra.obra_id == obra.id
        )
        .first()
    )
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado"
        )

    db.delete(miembro)
    db.commit()
    return None
