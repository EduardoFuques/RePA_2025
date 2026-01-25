# routes/persona_fisica_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.models.user_models import User
from src.models.persona_fisica_model import (
    PersonaFisica, SubperfilProductor, SubperfilDirector, 
    SubperfilGuionista, SubperfilDocumentalista, SubperfilRealizadorIntegral,
    SubperfilTecnicoArtistico, SubperfilCapacitador, SubperfilInvestigador
)
from src.schemas.persona_fisica_schemas import (
    PersonaFisicaCreate, PersonaFisicaUpdate, PersonaFisicaOut,
    ObraSubperfilCreate, ObraSubperfilOut,
    TecnicoArtisticoCreate, TecnicoArtisticoOut,
    CapacitadorCreate, CapacitadorOut,
    InvestigadorCreate, InvestigadorOut
)
from src.database import get_db
from src.utils import get_current_user

persona_fisica_router = APIRouter()


# === CRUD PERSONA FÍSICA ===

@persona_fisica_router.post("/", response_model=PersonaFisicaOut, status_code=status.HTTP_201_CREATED)
async def create_persona_fisica(
    data: PersonaFisicaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear registro de Persona Física para el usuario actual"""
    # Verificar que el usuario no tenga ya un registro
    existing = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un registro de Persona Física"
        )
    
    # Crear el registro
    db_persona = PersonaFisica(**data.model_dump(), user_id=current_user["id"])
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona


@persona_fisica_router.get("/me", response_model=PersonaFisicaOut)
async def get_my_persona_fisica(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el registro de Persona Física del usuario actual"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Persona Física"
        )
    return persona


@persona_fisica_router.put("/me", response_model=PersonaFisicaOut)
async def update_my_persona_fisica(
    data: PersonaFisicaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar el registro de Persona Física del usuario actual"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Persona Física"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(persona, key, value)
    
    db.commit()
    db.refresh(persona)
    return persona


@persona_fisica_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_persona_fisica(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar el registro de Persona Física del usuario actual"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Persona Física"
        )
    
    db.delete(persona)
    db.commit()
    return None


# === SUBPERFIL PRODUCTOR ===

@persona_fisica_router.post("/me/productor/obras", response_model=ObraSubperfilOut, status_code=status.HTTP_201_CREATED)
async def add_obra_productor(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar una obra al subperfil Productor"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = SubperfilProductor(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/productor/obras", response_model=List[ObraSubperfilOut])
async def get_obras_productor(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Productor"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    return db.query(SubperfilProductor).filter(SubperfilProductor.persona_fisica_id == persona.id).all()


@persona_fisica_router.delete("/me/productor/obras/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_obra_productor(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una obra del subperfil Productor"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = db.query(SubperfilProductor).filter(
        SubperfilProductor.id == obra_id,
        SubperfilProductor.persona_fisica_id == persona.id
    ).first()
    if not obra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")
    
    db.delete(obra)
    db.commit()
    return None


# === SUBPERFIL DIRECTOR ===

@persona_fisica_router.post("/me/director/obras", response_model=ObraSubperfilOut, status_code=status.HTTP_201_CREATED)
async def add_obra_director(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar una obra al subperfil Director"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = SubperfilDirector(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/director/obras", response_model=List[ObraSubperfilOut])
async def get_obras_director(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Director"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    return db.query(SubperfilDirector).filter(SubperfilDirector.persona_fisica_id == persona.id).all()


# === SUBPERFIL GUIONISTA ===

@persona_fisica_router.post("/me/guionista/obras", response_model=ObraSubperfilOut, status_code=status.HTTP_201_CREATED)
async def add_obra_guionista(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar una obra al subperfil Guionista"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = SubperfilGuionista(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/guionista/obras", response_model=List[ObraSubperfilOut])
async def get_obras_guionista(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Guionista"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    return db.query(SubperfilGuionista).filter(SubperfilGuionista.persona_fisica_id == persona.id).all()


# === SUBPERFIL DOCUMENTALISTA ===

@persona_fisica_router.post("/me/documentalista/obras", response_model=ObraSubperfilOut, status_code=status.HTTP_201_CREATED)
async def add_obra_documentalista(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar una obra al subperfil Documentalista"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = SubperfilDocumentalista(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/documentalista/obras", response_model=List[ObraSubperfilOut])
async def get_obras_documentalista(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Documentalista"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    return db.query(SubperfilDocumentalista).filter(SubperfilDocumentalista.persona_fisica_id == persona.id).all()


# === SUBPERFIL REALIZADOR INTEGRAL ===

@persona_fisica_router.post("/me/realizador-integral/obras", response_model=ObraSubperfilOut, status_code=status.HTTP_201_CREATED)
async def add_obra_realizador_integral(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar una obra al subperfil Realizador Integral"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    obra = SubperfilRealizadorIntegral(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/realizador-integral/obras", response_model=List[ObraSubperfilOut])
async def get_obras_realizador_integral(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Realizador Integral"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    return db.query(SubperfilRealizadorIntegral).filter(SubperfilRealizadorIntegral.persona_fisica_id == persona.id).all()


# === SUBPERFIL TÉCNICO/ARTÍSTICO ===

@persona_fisica_router.post("/me/tecnico-artistico", response_model=TecnicoArtisticoOut, status_code=status.HTTP_201_CREATED)
async def create_tecnico_artistico(
    data: TecnicoArtisticoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear/actualizar subperfil Técnico/Artístico"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    # Verificar si ya existe
    existing = db.query(SubperfilTecnicoArtistico).filter(
        SubperfilTecnicoArtistico.persona_fisica_id == persona.id
    ).first()
    
    if existing:
        # Actualizar
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    # Crear nuevo
    subperfil = SubperfilTecnicoArtistico(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(subperfil)
    db.commit()
    db.refresh(subperfil)
    return subperfil


@persona_fisica_router.get("/me/tecnico-artistico", response_model=TecnicoArtisticoOut)
async def get_tecnico_artistico(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener subperfil Técnico/Artístico"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    subperfil = db.query(SubperfilTecnicoArtistico).filter(
        SubperfilTecnicoArtistico.persona_fisica_id == persona.id
    ).first()
    if not subperfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado")
    
    return subperfil


# === SUBPERFIL CAPACITADOR ===

@persona_fisica_router.post("/me/capacitador", response_model=CapacitadorOut, status_code=status.HTTP_201_CREATED)
async def create_capacitador(
    data: CapacitadorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear/actualizar subperfil Capacitador"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    existing = db.query(SubperfilCapacitador).filter(
        SubperfilCapacitador.persona_fisica_id == persona.id
    ).first()
    
    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    subperfil = SubperfilCapacitador(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(subperfil)
    db.commit()
    db.refresh(subperfil)
    return subperfil


@persona_fisica_router.get("/me/capacitador", response_model=CapacitadorOut)
async def get_capacitador(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener subperfil Capacitador"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    subperfil = db.query(SubperfilCapacitador).filter(
        SubperfilCapacitador.persona_fisica_id == persona.id
    ).first()
    if not subperfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado")
    
    return subperfil


# === SUBPERFIL INVESTIGADOR ===

@persona_fisica_router.post("/me/investigador", response_model=InvestigadorOut, status_code=status.HTTP_201_CREATED)
async def create_investigador(
    data: InvestigadorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear/actualizar subperfil Investigador"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    existing = db.query(SubperfilInvestigador).filter(
        SubperfilInvestigador.persona_fisica_id == persona.id
    ).first()
    
    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    subperfil = SubperfilInvestigador(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(subperfil)
    db.commit()
    db.refresh(subperfil)
    return subperfil


@persona_fisica_router.get("/me/investigador", response_model=InvestigadorOut)
async def get_investigador(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener subperfil Investigador"""
    persona = db.query(PersonaFisica).filter(PersonaFisica.user_id == current_user["id"]).first()
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada")
    
    subperfil = db.query(SubperfilInvestigador).filter(
        SubperfilInvestigador.persona_fisica_id == persona.id
    ).first()
    if not subperfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado")
    
    return subperfil
