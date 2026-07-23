# routes/fomento_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from src.audit import audit_log
from src.database import get_db
from src.models.audit_model import AuditAction
from src.models.fomento_model import (
    AcompanamientoSemillero,
    CohorteSemillero,
    ComiteFomento,
    DictamenFomento,
    Evaluador,
    EventoFomento,
    LineaFomento,
    ParticipanteSemillero,
    TramiteFomento,
)
from src.schemas.fomento_schemas import (
    AcompanamientoSemilleroCreate,
    AcompanamientoSemilleroOut,
    AcompanamientoSemilleroUpdate,
    CohorteSemilleroCreate,
    CohorteSemilleroOut,
    CohorteSemilleroUpdate,
    ComiteFomentoCreate,
    ComiteFomentoOut,
    ComiteFomentoUpdate,
    DictamenFomentoCreate,
    DictamenFomentoOut,
    DictamenFomentoUpdate,
    EvaluadorCreate,
    EvaluadorOut,
    EvaluadorUpdate,
    EventoFomentoCreate,
    EventoFomentoOut,
    EventoFomentoUpdate,
    LineaFomentoCreate,
    LineaFomentoOut,
    LineaFomentoUpdate,
    ParticipanteSemilleroCreate,
    ParticipanteSemilleroOut,
    ParticipanteSemilleroUpdate,
    TramiteFomentoAdminUpdate,
    TramiteFomentoCreate,
    TramiteFomentoOut,
    TramiteFomentoUpdate,
)
from src.services.fomento_relational_service import (
    attach_comite_output_fields,
    attach_output_fields,
    sync_aportes,
    sync_integrantes,
    sync_pagos,
)
from src.utils import (
    check_any_permission,
    check_permissions,
    get_current_user,
    get_user_permissions,
)

fomento_router = APIRouter(prefix="/fomento", tags=["fomento"])


# === EVENTOS / CONVOCATORIAS ===


@fomento_router.post(
    "/eventos",
    response_model=EventoFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_evento(
    data: EventoFomentoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un Evento/Convocatoria (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    db_evento = EventoFomento(**data.model_dump())
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    return db_evento


@fomento_router.get("/eventos", response_model=list[EventoFomentoOut])
async def list_eventos(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar todos los Eventos (admin ve todos, usuario solo activos)"""
    query = db.query(EventoFomento).options(joinedload(EventoFomento.lineas))
    return query.order_by(EventoFomento.anio_edicion.desc()).all()


@fomento_router.get("/eventos/activos", response_model=list[EventoFomentoOut])
async def list_eventos_activos(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar Eventos activos (para el formulario de trámite)"""
    return (
        db.query(EventoFomento)
        .options(joinedload(EventoFomento.lineas))
        .filter(EventoFomento.estado == "activo")
        .order_by(EventoFomento.anio_edicion.desc())
        .all()
    )


@fomento_router.get("/eventos/{evento_id}", response_model=EventoFomentoOut)
async def get_evento(
    evento_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Evento por ID"""
    evento = (
        db.query(EventoFomento)
        .options(joinedload(EventoFomento.lineas))
        .filter(EventoFomento.id == evento_id)
        .first()
    )
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado"
        )
    return evento


@fomento_router.put("/eventos/{evento_id}", response_model=EventoFomentoOut)
async def update_evento(
    evento_id: int,
    data: EventoFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Evento (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    evento = db.query(EventoFomento).filter(EventoFomento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(evento, key, value)

    db.commit()
    db.refresh(evento)
    return evento


@fomento_router.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evento(
    evento_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Evento y sus líneas (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    evento = db.query(EventoFomento).filter(EventoFomento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado"
        )
    db.delete(evento)
    db.commit()
    return None


# === LÍNEAS DE FOMENTO ===


@fomento_router.post(
    "/eventos/{evento_id}/lineas",
    response_model=LineaFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_linea(
    evento_id: int,
    data: LineaFomentoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear una Línea dentro de un Evento (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    evento = db.query(EventoFomento).filter(EventoFomento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado"
        )
    db_linea = LineaFomento(**data.model_dump(), evento_id=evento_id)
    db.add(db_linea)
    db.commit()
    db.refresh(db_linea)
    return db_linea


@fomento_router.get("/eventos/{evento_id}/lineas", response_model=list[LineaFomentoOut])
async def list_lineas(
    evento_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar Líneas de un Evento"""
    return db.query(LineaFomento).filter(LineaFomento.evento_id == evento_id).all()


@fomento_router.put("/lineas/{linea_id}", response_model=LineaFomentoOut)
async def update_linea(
    linea_id: int,
    data: LineaFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar una Línea (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    linea = db.query(LineaFomento).filter(LineaFomento.id == linea_id).first()
    if not linea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Línea no encontrada"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(linea, key, value)

    db.commit()
    db.refresh(linea)
    return linea


@fomento_router.delete("/lineas/{linea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_linea(
    linea_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una Línea (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    linea = db.query(LineaFomento).filter(LineaFomento.id == linea_id).first()
    if not linea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Línea no encontrada"
        )
    db.delete(linea)
    db.commit()
    return None


# === TRÁMITE DE FOMENTO ===


@fomento_router.post(
    "/tramites",
    response_model=TramiteFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_tramite(
    data: TramiteFomentoCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un nuevo Trámite de Fomento"""
    tramite_data = data.model_dump(exclude={"otros_aportes_no_iaavim"})
    db_tramite = TramiteFomento(**tramite_data, user_id=current_user["id"])
    db.add(db_tramite)
    db.flush()
    sync_aportes(db, db_tramite, data.otros_aportes_no_iaavim)
    audit_log(
        db=db,
        action=AuditAction.CREATE,
        user_id=current_user["id"],
        resource_type="TramiteFomento",
        resource_id=str(db_tramite.id),
        details={"titulo_proyecto": data.titulo_proyecto, "borrador": data.borrador},
        request=request,
    )
    db.commit()
    db.refresh(db_tramite)
    return attach_output_fields(db_tramite)


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
    return attach_output_fields(tramite)


@fomento_router.put("/tramites/me", response_model=TramiteFomentoOut)
async def update_my_tramite(
    data: TramiteFomentoUpdate,
    request: Request,
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

    update_data = data.model_dump(exclude_unset=True, exclude={"otros_aportes_no_iaavim"})
    for key, value in update_data.items():
        setattr(tramite, key, value)
    sync_aportes(db, tramite, data.otros_aportes_no_iaavim)

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="TramiteFomento",
        resource_id=str(tramite.id),
        details={"campos": sorted(update_data.keys())},
        request=request,
    )
    db.commit()
    db.refresh(tramite)
    return attach_output_fields(tramite)


@fomento_router.get("/tramites", response_model=list[TramiteFomentoOut])
async def list_tramites(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los Trámites de Fomento del usuario"""
    tramites = (
        db.query(TramiteFomento)
        .filter(TramiteFomento.user_id == current_user["id"])
        .all()
    )
    return [attach_output_fields(t) for t in tramites]


@fomento_router.get("/tramites/admin", response_model=list[TramiteFomentoOut])
async def list_all_tramites(
    tipo_tramite: str | None = None,
    estado_tramite: str | None = None,
    evento_id: int | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar TODOS los Trámites de Fomento (admin, gestor_fomento o evaluador)"""
    check_permissions(db, current_user, "tramites:read_all")
    query = db.query(TramiteFomento)
    if tipo_tramite:
        query = query.filter(TramiteFomento.tipo_tramite == tipo_tramite)
    if estado_tramite:
        query = query.filter(TramiteFomento.estado_tramite == estado_tramite)
    if evento_id:
        query = query.filter(TramiteFomento.evento_id == evento_id)
    tramites = query.order_by(TramiteFomento.created_at.desc()).all()
    return [attach_output_fields(t) for t in tramites]


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
    return attach_output_fields(tramite)


@fomento_router.put("/tramites/{tramite_id}", response_model=TramiteFomentoOut)
async def update_tramite(
    tramite_id: int,
    data: TramiteFomentoUpdate,
    request: Request,
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

    update_data = data.model_dump(exclude_unset=True, exclude={"otros_aportes_no_iaavim"})
    for key, value in update_data.items():
        setattr(tramite, key, value)
    sync_aportes(db, tramite, data.otros_aportes_no_iaavim)

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="TramiteFomento",
        resource_id=str(tramite.id),
        details={"campos": sorted(update_data.keys())},
        request=request,
    )
    db.commit()
    db.refresh(tramite)
    return attach_output_fields(tramite)


@fomento_router.get("/tramites/{tramite_id}/admin", response_model=TramiteFomentoOut)
async def admin_get_tramite(
    tramite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """[Gestión] Obtener cualquier Trámite de Fomento por ID (sin filtrar por
    titular). Requiere fomento:manage — es la contraparte de lectura de
    admin_update_tramite, para la pantalla de detalle del backoffice."""
    check_permissions(db, current_user, "fomento:manage")
    tramite = db.query(TramiteFomento).filter(TramiteFomento.id == tramite_id).first()
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )
    return attach_output_fields(tramite)


@fomento_router.put("/tramites/{tramite_id}/admin", response_model=TramiteFomentoOut)
async def admin_update_tramite(
    tramite_id: int,
    data: TramiteFomentoAdminUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """[Gestión] Actualizar cualquier Trámite de Fomento, incluidos los campos
    administrativos del expediente (estado, montos aprobados, resoluciones,
    pagos, vinculaciones interáreas). Requiere fomento:manage (admin o
    gestor_fomento). Todo cambio queda auditado."""
    check_permissions(db, current_user, "fomento:manage")

    tramite = (
        db.query(TramiteFomento).filter(TramiteFomento.id == tramite_id).first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )

    update_data = data.model_dump(exclude_unset=True, exclude={"pagos"})
    cambios_estado = {
        k: {"antes": getattr(tramite, k), "despues": v}
        for k, v in update_data.items()
        if k in ("estado_tramite", "monto_aprobado_iaavim", "nro_expediente")
        and getattr(tramite, k) != v
    }
    for key, value in update_data.items():
        setattr(tramite, key, value)

    pagos_antes = len(tramite.pagos_rel)
    sync_pagos(db, tramite, data.pagos)
    if data.pagos is not None and len(data.pagos) != pagos_antes:
        cambios_estado["pagos"] = {"antes": pagos_antes, "despues": len(data.pagos)}

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="TramiteFomento",
        resource_id=str(tramite.id),
        details={
            "admin": True,
            "titular": tramite.user_id,
            "campos": sorted(update_data.keys()),
            **({"cambios_clave": cambios_estado} if cambios_estado else {}),
        },
        request=request,
    )
    db.commit()
    db.refresh(tramite)
    return attach_output_fields(tramite)


@fomento_router.delete("/tramites/{tramite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tramite(
    tramite_id: int,
    request: Request,
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

    titulo = tramite.titulo_proyecto
    db.delete(tramite)
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="TramiteFomento",
        resource_id=str(tramite_id),
        details={"titulo_proyecto": titulo},
        request=request,
    )
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


@fomento_router.get("/evaluadores/todos", response_model=list[EvaluadorOut])
async def list_all_evaluadores(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Listar todos los Evaluadores del sistema (solo admin, para asignar a comités)"""
    check_permissions(db, current_user, "fomento:manage")
    return (
        db.query(Evaluador)
        .filter(Evaluador.borrador.is_(False))
        .order_by(Evaluador.nombre_completo)
        .all()
    )


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


# === COMITÉS DE FOMENTO ===


@fomento_router.post(
    "/comites",
    response_model=ComiteFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_comite(
    data: ComiteFomentoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un Comité de evaluación (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    evento = db.query(EventoFomento).filter(EventoFomento.id == data.evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado"
        )
    comite_data = data.model_dump(exclude={"integrantes"})
    db_comite = ComiteFomento(**comite_data)
    db.add(db_comite)
    db.flush()  # necesita comite.id real para las FKs de IntegranteComite
    sync_integrantes(db, db_comite, data.integrantes)
    db.commit()
    db.refresh(db_comite)
    return attach_comite_output_fields(db_comite)


@fomento_router.get("/comites", response_model=list[ComiteFomentoOut])
async def list_comites(
    evento_id: int | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar Comités (solo admin). Opcionalmente filtrar por evento."""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    query = db.query(ComiteFomento)
    if evento_id:
        query = query.filter(ComiteFomento.evento_id == evento_id)
    comites = query.order_by(ComiteFomento.created_at.desc()).all()
    return [attach_comite_output_fields(c) for c in comites]


@fomento_router.get("/comites/{comite_id}", response_model=ComiteFomentoOut)
async def get_comite(
    comite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Comité por ID (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    comite = db.query(ComiteFomento).filter(ComiteFomento.id == comite_id).first()
    if not comite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comité no encontrado"
        )
    return attach_comite_output_fields(comite)


@fomento_router.put("/comites/{comite_id}", response_model=ComiteFomentoOut)
async def update_comite(
    comite_id: int,
    data: ComiteFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Comité (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    comite = db.query(ComiteFomento).filter(ComiteFomento.id == comite_id).first()
    if not comite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comité no encontrado"
        )
    update_data = data.model_dump(exclude_unset=True, exclude={"integrantes"})
    for key, value in update_data.items():
        setattr(comite, key, value)
    sync_integrantes(db, comite, data.integrantes)
    db.commit()
    db.refresh(comite)
    return attach_comite_output_fields(comite)


@fomento_router.delete("/comites/{comite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comite(
    comite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Comité (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    comite = db.query(ComiteFomento).filter(ComiteFomento.id == comite_id).first()
    if not comite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comité no encontrado"
        )
    db.delete(comite)
    db.commit()
    return None


# === DICTÁMENES DE FOMENTO ===


@fomento_router.post(
    "/dictamenes",
    response_model=DictamenFomentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_dictamen(
    data: DictamenFomentoCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un Dictamen (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    tramite = (
        db.query(TramiteFomento).filter(TramiteFomento.id == data.tramite_id).first()
    )
    if not tramite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado"
        )
    evaluador = db.query(Evaluador).filter(Evaluador.id == data.evaluador_id).first()
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evaluador no encontrado"
        )
    db_dictamen = DictamenFomento(**data.model_dump())
    db.add(db_dictamen)
    db.commit()
    db.refresh(db_dictamen)
    return db_dictamen


@fomento_router.get("/dictamenes", response_model=list[DictamenFomentoOut])
async def list_dictamenes(
    tramite_id: int | None = None,
    evaluador_id: int | None = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar Dictámenes (solo admin). Filtrar por trámite o evaluador."""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    query = db.query(DictamenFomento)
    if tramite_id:
        query = query.filter(DictamenFomento.tramite_id == tramite_id)
    if evaluador_id:
        query = query.filter(DictamenFomento.evaluador_id == evaluador_id)
    return query.order_by(DictamenFomento.created_at.desc()).all()


@fomento_router.get(
    "/tramites/{tramite_id}/dictamenes",
    response_model=list[DictamenFomentoOut],
)
async def get_dictamenes_by_tramite(
    tramite_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener dictámenes de un trámite (gestión/evaluación ve todos, ciudadano ve devolucionados)"""
    query = db.query(DictamenFomento).filter(DictamenFomento.tramite_id == tramite_id)
    user_perms = get_user_permissions(db, current_user)
    if not user_perms.intersection({"fomento:manage", "tramites:evaluate"}):
        query = query.filter(DictamenFomento.devolucion_presentante)
    return query.order_by(DictamenFomento.fecha.desc()).all()


@fomento_router.get("/dictamenes/{dictamen_id}", response_model=DictamenFomentoOut)
async def get_dictamen(
    dictamen_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un Dictamen por ID (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    dictamen = (
        db.query(DictamenFomento).filter(DictamenFomento.id == dictamen_id).first()
    )
    if not dictamen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictamen no encontrado",
        )
    return dictamen


@fomento_router.put("/dictamenes/{dictamen_id}", response_model=DictamenFomentoOut)
async def update_dictamen(
    dictamen_id: int,
    data: DictamenFomentoUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un Dictamen (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    dictamen = (
        db.query(DictamenFomento).filter(DictamenFomento.id == dictamen_id).first()
    )
    if not dictamen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictamen no encontrado",
        )
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dictamen, key, value)
    db.commit()
    db.refresh(dictamen)
    return dictamen


@fomento_router.delete(
    "/dictamenes/{dictamen_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_dictamen(
    dictamen_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un Dictamen (solo admin)"""
    check_any_permission(db, current_user, "fomento:manage", "tramites:evaluate")
    dictamen = (
        db.query(DictamenFomento).filter(DictamenFomento.id == dictamen_id).first()
    )
    if not dictamen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dictamen no encontrado",
        )
    db.delete(dictamen)
    db.commit()
    return None


# === SEMILLERO — COHORTES ===


@fomento_router.post(
    "/cohortes",
    response_model=CohorteSemilleroOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_cohorte(
    data: CohorteSemilleroCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear una Cohorte del Semillero (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    db_cohorte = CohorteSemillero(**data.model_dump())
    db.add(db_cohorte)
    db.commit()
    db.refresh(db_cohorte)
    return db_cohorte


@fomento_router.get("/cohortes", response_model=list[CohorteSemilleroOut])
async def list_cohortes(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar Cohortes (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    return (
        db.query(CohorteSemillero).order_by(CohorteSemillero.anio_edicion.desc()).all()
    )


@fomento_router.get("/cohortes/{cohorte_id}", response_model=CohorteSemilleroOut)
async def get_cohorte(
    cohorte_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener una Cohorte por ID (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    cohorte = (
        db.query(CohorteSemillero).filter(CohorteSemillero.id == cohorte_id).first()
    )
    if not cohorte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada"
        )
    return cohorte


@fomento_router.put("/cohortes/{cohorte_id}", response_model=CohorteSemilleroOut)
async def update_cohorte(
    cohorte_id: int,
    data: CohorteSemilleroUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar una Cohorte (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    cohorte = (
        db.query(CohorteSemillero).filter(CohorteSemillero.id == cohorte_id).first()
    )
    if not cohorte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada"
        )
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cohorte, key, value)
    db.commit()
    db.refresh(cohorte)
    return cohorte


@fomento_router.delete("/cohortes/{cohorte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohorte(
    cohorte_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar una Cohorte (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    cohorte = (
        db.query(CohorteSemillero).filter(CohorteSemillero.id == cohorte_id).first()
    )
    if not cohorte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada"
        )
    db.delete(cohorte)
    db.commit()
    return None


# === SEMILLERO — PARTICIPANTES ===


@fomento_router.post(
    "/cohortes/{cohorte_id}/participantes",
    response_model=ParticipanteSemilleroOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_participante(
    cohorte_id: int,
    data: ParticipanteSemilleroCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agregar participante a una Cohorte (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    cohorte = (
        db.query(CohorteSemillero).filter(CohorteSemillero.id == cohorte_id).first()
    )
    if not cohorte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada"
        )
    payload = data.model_dump()
    payload["cohorte_id"] = cohorte_id
    db_part = ParticipanteSemillero(**payload)
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


@fomento_router.get(
    "/cohortes/{cohorte_id}/participantes",
    response_model=list[ParticipanteSemilleroOut],
)
async def list_participantes(
    cohorte_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar participantes de una Cohorte (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    return (
        db.query(ParticipanteSemillero)
        .filter(ParticipanteSemillero.cohorte_id == cohorte_id)
        .order_by(ParticipanteSemillero.nombre_completo)
        .all()
    )


@fomento_router.put(
    "/participantes/{participante_id}",
    response_model=ParticipanteSemilleroOut,
)
async def update_participante(
    participante_id: int,
    data: ParticipanteSemilleroUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un participante (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    part = (
        db.query(ParticipanteSemillero)
        .filter(ParticipanteSemillero.id == participante_id)
        .first()
    )
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participante no encontrado",
        )
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(part, key, value)
    db.commit()
    db.refresh(part)
    return part


@fomento_router.delete(
    "/participantes/{participante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_participante(
    participante_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un participante (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    part = (
        db.query(ParticipanteSemillero)
        .filter(ParticipanteSemillero.id == participante_id)
        .first()
    )
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participante no encontrado",
        )
    db.delete(part)
    db.commit()
    return None


# === SEMILLERO — ACOMPAÑAMIENTOS ===


@fomento_router.post(
    "/participantes/{participante_id}/acompanamientos",
    response_model=AcompanamientoSemilleroOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_acompanamiento(
    participante_id: int,
    data: AcompanamientoSemilleroCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registrar un acompañamiento para un participante (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    part = (
        db.query(ParticipanteSemillero)
        .filter(ParticipanteSemillero.id == participante_id)
        .first()
    )
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participante no encontrado",
        )
    payload = data.model_dump()
    payload["participante_id"] = participante_id
    db_acomp = AcompanamientoSemillero(**payload)
    db.add(db_acomp)
    db.commit()
    db.refresh(db_acomp)
    return db_acomp


@fomento_router.get(
    "/participantes/{participante_id}/acompanamientos",
    response_model=list[AcompanamientoSemilleroOut],
)
async def list_acompanamientos(
    participante_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar acompañamientos de un participante (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    return (
        db.query(AcompanamientoSemillero)
        .filter(AcompanamientoSemillero.participante_id == participante_id)
        .order_by(AcompanamientoSemillero.fecha.desc())
        .all()
    )


@fomento_router.put(
    "/acompanamientos/{acompanamiento_id}",
    response_model=AcompanamientoSemilleroOut,
)
async def update_acompanamiento(
    acompanamiento_id: int,
    data: AcompanamientoSemilleroUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un acompañamiento (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    acomp = (
        db.query(AcompanamientoSemillero)
        .filter(AcompanamientoSemillero.id == acompanamiento_id)
        .first()
    )
    if not acomp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acompañamiento no encontrado",
        )
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(acomp, key, value)
    db.commit()
    db.refresh(acomp)
    return acomp


@fomento_router.delete(
    "/acompanamientos/{acompanamiento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_acompanamiento(
    acompanamiento_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un acompañamiento (solo admin)"""
    check_permissions(db, current_user, "fomento:manage")
    acomp = (
        db.query(AcompanamientoSemillero)
        .filter(AcompanamientoSemillero.id == acompanamiento_id)
        .first()
    )
    if not acomp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acompañamiento no encontrado",
        )
    db.delete(acomp)
    db.commit()
    return None
