"""
Rutas para el formulario de Persona Física del RePA.

Permite a los usuarios registrar sus datos personales, situación laboral,
y seleccionar subperfiles según su rol en el sector audiovisual.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.crud_helpers import (
    apply_update_fields,
    check_duplicate_record,
    commit_or_conflict,
    create_registrable_record,
    delete_record,
    get_user_record,
    integrity_as_conflict,
)
from src.database import get_db
from src.models.persona_fisica_model import (
    PersonaFisica,
    SubperfilCapacitador,
    SubperfilDirector,
    SubperfilDocumentalista,
    SubperfilGuionista,
    SubperfilInvestigador,
    SubperfilProductor,
    SubperfilRealizadorIntegral,
    SubperfilTecnicoArtistico,
)
from src.rate_limiter import limiter
from src.schemas.persona_fisica_schemas import (
    CapacitadorCreate,
    CapacitadorOut,
    InvestigadorCreate,
    InvestigadorOut,
    ObraSubperfilCreate,
    ObraSubperfilOut,
    PersonaFisicaCreate,
    PersonaFisicaOut,
    PersonaFisicaSearchOut,
    PersonaFisicaUpdate,
    TecnicoArtisticoCreate,
    TecnicoArtisticoOut,
)
from src.services import lifecycle_service
from src.utils import get_current_user

persona_fisica_router = APIRouter()

# Mensajes de error reutilizables
MSG_NOT_FOUND = "No se encontró registro de Persona Física"
MSG_DUPLICATE = "El usuario ya tiene un registro de Persona Física"


# === CRUD PERSONA FÍSICA ===


@persona_fisica_router.post(
    "/",
    response_model=PersonaFisicaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de Persona Física",
    responses={
        201: {"description": "Registro creado exitosamente"},
        400: {"description": "El usuario ya tiene un registro"},
        401: {"description": "No autenticado"},
    },
)
async def create_persona_fisica(
    data: PersonaFisicaCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crear el registro de Persona Física para el usuario autenticado.

    Incluye datos personales, identidades, situación laboral e interés institucional.
    Cada usuario solo puede tener **un registro** de Persona Física.
    """
    check_duplicate_record(db, PersonaFisica, current_user["id"], MSG_DUPLICATE)
    return create_registrable_record(
        db,
        PersonaFisica,
        data,
        current_user["id"],
        on_flush=lambda r, ud: lifecycle_service.procesar_actualizacion(db, r, ud),
    )


@persona_fisica_router.get("/me", response_model=PersonaFisicaOut)
async def get_my_persona_fisica(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el registro de Persona Física del usuario actual"""
    return get_user_record(db, PersonaFisica, current_user["id"], MSG_NOT_FOUND)


@persona_fisica_router.put("/me", response_model=PersonaFisicaOut)
async def update_my_persona_fisica(
    data: PersonaFisicaUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el registro de Persona Física del usuario actual.

    Al enviar el formulario (borrador: false por primera vez) emite el
    código RePA de la persona — PF es el primer formulario obligatorio,
    así que este código queda disponible para que PJ/AS/AGAM lo hereden."""
    persona = get_user_record(db, PersonaFisica, current_user["id"], MSG_NOT_FOUND)
    update_data = apply_update_fields(persona, data)
    with integrity_as_conflict(db):
        lifecycle_service.procesar_actualizacion(db, persona, update_data)
    commit_or_conflict(db)
    db.refresh(persona)
    return persona


@persona_fisica_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_persona_fisica(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Eliminar el registro de Persona Física del usuario actual"""
    persona = get_user_record(db, PersonaFisica, current_user["id"], MSG_NOT_FOUND)
    delete_record(db, persona)
    return None


# === BÚSQUEDA DE PERSONAS REGISTRADAS ===


@persona_fisica_router.get("/search", response_model=list[PersonaFisicaSearchOut])
@limiter.limit("30/minute")
async def search_personas_fisicas(
    request: Request,
    q: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Buscar personas físicas registradas en el RePA por nombre, apellido o DNI.
    Retorna resultados parciales (máximo 10) para uso en buscador de integrantes.

    Se puede buscar POR documento, pero la respuesta no lo devuelve: sale solo
    id, nombre y apellido (ver PersonaFisicaSearchOut). Quien ya conoce un DNI
    puede confirmar a quién pertenece, que es inherente a un buscador; lo que
    ya no se puede es recorrer el padrón juntando documentos y correos ajenos.

    El límite de 30/min por IP se mantiene como segunda barrera contra el
    barrido sistemático de nombres.
    """
    if not q or len(q.strip()) < 2:
        return []

    term = f"%{q.strip()}%"
    # Strip dots from search term for DNI matching (e.g. "38778" should match "38.778.767")
    term_no_dots = f"%{q.strip().replace('.', '')}%"
    results = (
        db.query(PersonaFisica)
        .filter(
            PersonaFisica.borrador == False,  # noqa: E712
            (
                PersonaFisica.nombre.ilike(term)
                | PersonaFisica.apellido.ilike(term)
                | PersonaFisica.dni.ilike(term)
                | func.replace(PersonaFisica.dni, ".", "").ilike(term_no_dots)
            ),
        )
        .limit(10)
        .all()
    )
    return results


# === SUBPERFIL PRODUCTOR ===


@persona_fisica_router.post(
    "/me/productor/obras",
    response_model=ObraSubperfilOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_obra_productor(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar una obra al subperfil Productor"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = SubperfilProductor(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/productor/obras", response_model=list[ObraSubperfilOut])
async def get_obras_productor(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Productor"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    return (
        db.query(SubperfilProductor)
        .filter(SubperfilProductor.persona_fisica_id == persona.id)
        .all()
    )


@persona_fisica_router.delete(
    "/me/productor/obras/{obra_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_obra_productor(
    obra_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una obra del subperfil Productor"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = (
        db.query(SubperfilProductor)
        .filter(
            SubperfilProductor.id == obra_id,
            SubperfilProductor.persona_fisica_id == persona.id,
        )
        .first()
    )
    if not obra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada"
        )

    db.delete(obra)
    db.commit()
    return None


# === SUBPERFIL DIRECTOR ===


@persona_fisica_router.post(
    "/me/director/obras",
    response_model=ObraSubperfilOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_obra_director(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar una obra al subperfil Director"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = SubperfilDirector(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/director/obras", response_model=list[ObraSubperfilOut])
async def get_obras_director(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Director"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    return (
        db.query(SubperfilDirector)
        .filter(SubperfilDirector.persona_fisica_id == persona.id)
        .all()
    )


# === SUBPERFIL GUIONISTA ===


@persona_fisica_router.post(
    "/me/guionista/obras",
    response_model=ObraSubperfilOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_obra_guionista(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar una obra al subperfil Guionista"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = SubperfilGuionista(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get("/me/guionista/obras", response_model=list[ObraSubperfilOut])
async def get_obras_guionista(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Guionista"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    return (
        db.query(SubperfilGuionista)
        .filter(SubperfilGuionista.persona_fisica_id == persona.id)
        .all()
    )


# === SUBPERFIL DOCUMENTALISTA ===


@persona_fisica_router.post(
    "/me/documentalista/obras",
    response_model=ObraSubperfilOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_obra_documentalista(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar una obra al subperfil Documentalista"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = SubperfilDocumentalista(**data.model_dump(), persona_fisica_id=persona.id)
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get(
    "/me/documentalista/obras", response_model=list[ObraSubperfilOut]
)
async def get_obras_documentalista(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Documentalista"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    return (
        db.query(SubperfilDocumentalista)
        .filter(SubperfilDocumentalista.persona_fisica_id == persona.id)
        .all()
    )


# === SUBPERFIL REALIZADOR INTEGRAL ===


@persona_fisica_router.post(
    "/me/realizador-integral/obras",
    response_model=ObraSubperfilOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_obra_realizador_integral(
    data: ObraSubperfilCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar una obra al subperfil Realizador Integral"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    obra = SubperfilRealizadorIntegral(
        **data.model_dump(), persona_fisica_id=persona.id
    )
    db.add(obra)
    db.commit()
    db.refresh(obra)
    return obra


@persona_fisica_router.get(
    "/me/realizador-integral/obras", response_model=list[ObraSubperfilOut]
)
async def get_obras_realizador_integral(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener obras del subperfil Realizador Integral"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    return (
        db.query(SubperfilRealizadorIntegral)
        .filter(SubperfilRealizadorIntegral.persona_fisica_id == persona.id)
        .all()
    )


# === SUBPERFIL TÉCNICO/ARTÍSTICO ===


@persona_fisica_router.post(
    "/me/tecnico-artistico",
    response_model=TecnicoArtisticoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_tecnico_artistico(
    data: TecnicoArtisticoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear/actualizar subperfil Técnico/Artístico"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    # Verificar si ya existe
    existing = (
        db.query(SubperfilTecnicoArtistico)
        .filter(SubperfilTecnicoArtistico.persona_fisica_id == persona.id)
        .first()
    )

    if existing:
        # Actualizar
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    # Crear nuevo
    subperfil = SubperfilTecnicoArtistico(
        **data.model_dump(), persona_fisica_id=persona.id
    )
    db.add(subperfil)
    db.commit()
    db.refresh(subperfil)
    return subperfil


@persona_fisica_router.get("/me/tecnico-artistico", response_model=TecnicoArtisticoOut)
async def get_tecnico_artistico(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener subperfil Técnico/Artístico"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    subperfil = (
        db.query(SubperfilTecnicoArtistico)
        .filter(SubperfilTecnicoArtistico.persona_fisica_id == persona.id)
        .first()
    )
    if not subperfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado"
        )

    return subperfil


# === SUBPERFIL CAPACITADOR ===


@persona_fisica_router.post(
    "/me/capacitador",
    response_model=CapacitadorOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_capacitador(
    data: CapacitadorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear/actualizar subperfil Capacitador"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    existing = (
        db.query(SubperfilCapacitador)
        .filter(SubperfilCapacitador.persona_fisica_id == persona.id)
        .first()
    )

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
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener subperfil Capacitador"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    subperfil = (
        db.query(SubperfilCapacitador)
        .filter(SubperfilCapacitador.persona_fisica_id == persona.id)
        .first()
    )
    if not subperfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado"
        )

    return subperfil


# === SUBPERFIL INVESTIGADOR ===


@persona_fisica_router.post(
    "/me/investigador",
    response_model=InvestigadorOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_investigador(
    data: InvestigadorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear/actualizar subperfil Investigador"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    existing = (
        db.query(SubperfilInvestigador)
        .filter(SubperfilInvestigador.persona_fisica_id == persona.id)
        .first()
    )

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
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener subperfil Investigador"""
    persona = (
        db.query(PersonaFisica)
        .filter(PersonaFisica.user_id == current_user["id"])
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persona Física no encontrada"
        )

    subperfil = (
        db.query(SubperfilInvestigador)
        .filter(SubperfilInvestigador.persona_fisica_id == persona.id)
        .first()
    )
    if not subperfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subperfil no encontrado"
        )

    return subperfil
