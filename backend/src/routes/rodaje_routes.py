"""
Rutas para Comisión de Filmaciones - Archivo de Rodajes de Misiones.

Permite registrar, gestionar y monitorear los rodajes audiovisuales
realizados en la provincia de Misiones.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.audit import audit_log
from src.database import get_db
from src.models.audit_model import AuditAction
from src.models.rodaje_model import Rodaje
from src.schemas.rodaje_schemas import (
    RodajeAdminUpdate,
    RodajeCreate,
    RodajeListOut,
    RodajeOut,
    RodajeUpdate,
)
from src.utils import check_permissions, get_current_user

rodaje_router = APIRouter()

MSG_NOT_FOUND = "No se encontró el registro de rodaje"


# === CRUD RODAJE (Usuario) ===


@rodaje_router.post(
    "/",
    response_model=RodajeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de rodaje",
    responses={
        201: {"description": "Rodaje registrado exitosamente"},
        401: {"description": "No autenticado"},
    },
)
async def create_rodaje(
    data: RodajeCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crear un nuevo registro de rodaje (Alta o Finalización).

    Un usuario puede tener múltiples rodajes registrados.
    """
    rodaje_data = data.model_dump()

    # Convertir locaciones a formato JSON si existe
    if rodaje_data.get("locaciones"):
        rodaje_data["locaciones"] = [
            loc.model_dump() if hasattr(loc, "model_dump") else loc
            for loc in rodaje_data["locaciones"]
        ]

    rodaje = Rodaje(**rodaje_data, user_id=current_user["id"])
    db.add(rodaje)
    db.flush()
    audit_log(
        db=db,
        action=AuditAction.CREATE,
        user_id=current_user["id"],
        resource_type="Rodaje",
        resource_id=str(rodaje.id),
        details={
            "titulo_produccion": data.titulo_produccion,
            "borrador": data.borrador,
        },
        request=request,
    )
    db.commit()
    db.refresh(rodaje)
    return rodaje


@rodaje_router.get(
    "/me", response_model=list[RodajeListOut], summary="Listar mis rodajes"
)
async def get_my_rodajes(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener todos los rodajes del usuario actual"""
    return (
        db.query(Rodaje)
        .filter(Rodaje.user_id == current_user["id"])
        .order_by(Rodaje.created_at.desc())
        .all()
    )


@rodaje_router.get(
    "/me/{rodaje_id}", response_model=RodajeOut, summary="Obtener detalle de un rodaje"
)
async def get_my_rodaje(
    rodaje_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un rodaje específico del usuario actual"""
    rodaje = (
        db.query(Rodaje)
        .filter(Rodaje.id == rodaje_id, Rodaje.user_id == current_user["id"])
        .first()
    )

    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    return rodaje


@rodaje_router.put(
    "/me/{rodaje_id}", response_model=RodajeOut, summary="Actualizar un rodaje"
)
async def update_my_rodaje(
    rodaje_id: int,
    data: RodajeUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un rodaje del usuario actual"""
    rodaje = (
        db.query(Rodaje)
        .filter(Rodaje.id == rodaje_id, Rodaje.user_id == current_user["id"])
        .first()
    )

    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    update_data = data.model_dump(exclude_unset=True)

    # Convertir locaciones a formato JSON si existe
    if "locaciones" in update_data and update_data["locaciones"]:
        update_data["locaciones"] = [
            loc.model_dump() if hasattr(loc, "model_dump") else loc
            for loc in update_data["locaciones"]
        ]

    for key, value in update_data.items():
        setattr(rodaje, key, value)

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="Rodaje",
        resource_id=str(rodaje.id),
        details={"campos": sorted(update_data.keys())},
        request=request,
    )
    db.commit()
    db.refresh(rodaje)
    return rodaje


@rodaje_router.delete(
    "/me/{rodaje_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un rodaje",
)
async def delete_my_rodaje(
    rodaje_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un rodaje del usuario actual (solo si es borrador)"""
    rodaje = (
        db.query(Rodaje)
        .filter(Rodaje.id == rodaje_id, Rodaje.user_id == current_user["id"])
        .first()
    )

    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    # Solo permitir eliminar borradores
    if not rodaje.borrador:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden eliminar rodajes en estado borrador",
        )

    titulo = rodaje.titulo_produccion
    db.delete(rodaje)
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="Rodaje",
        resource_id=str(rodaje_id),
        details={"titulo_produccion": titulo},
        request=request,
    )
    db.commit()
    return None


# === RUTAS ADMIN ===


@rodaje_router.get(
    "/admin/all",
    response_model=list[RodajeListOut],
    summary="[Admin] Listar todos los rodajes",
)
async def admin_get_all_rodajes(
    estado: str = None,
    anio: int = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    [Admin] Obtener todos los rodajes registrados.

    Filtros opcionales:
    - estado: recibido, en_evaluacion, aprobado, condicionado, denegado, finalizado
    - anio: Año de rodaje
    """
    check_permissions(db, current_user, "rodajes:manage")

    query = db.query(Rodaje)

    if estado:
        query = query.filter(Rodaje.estado_tramite == estado)
    if anio:
        query = query.filter(Rodaje.anio_rodaje == anio)

    return query.order_by(Rodaje.created_at.desc()).all()


@rodaje_router.get(
    "/admin/{rodaje_id}",
    response_model=RodajeOut,
    summary="[Admin] Obtener detalle de un rodaje",
)
async def admin_get_rodaje(
    rodaje_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """[Admin] Obtener cualquier rodaje por ID"""
    check_permissions(db, current_user, "rodajes:manage")

    rodaje = db.query(Rodaje).filter(Rodaje.id == rodaje_id).first()
    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    return rodaje


@rodaje_router.put(
    "/admin/{rodaje_id}",
    response_model=RodajeOut,
    summary="[Admin] Actualizar un rodaje",
)
async def admin_update_rodaje(
    rodaje_id: int,
    data: RodajeAdminUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    [Admin] Actualizar cualquier rodaje.

    Único punto de entrada para los campos de seguimiento (estado_tramite,
    fecha_evaluacion, fecha_emision_permiso, inspector_asignado, pagos,
    observaciones_internas). Todo cambio queda auditado.
    """
    check_permissions(db, current_user, "rodajes:manage")

    rodaje = db.query(Rodaje).filter(Rodaje.id == rodaje_id).first()
    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    update_data = data.model_dump(exclude_unset=True)

    # Convertir locaciones a formato JSON si existe
    if "locaciones" in update_data and update_data["locaciones"]:
        update_data["locaciones"] = [
            loc.model_dump() if hasattr(loc, "model_dump") else loc
            for loc in update_data["locaciones"]
        ]

    cambios_estado = {
        k: {"antes": getattr(rodaje, k), "despues": v}
        for k, v in update_data.items()
        if k in ("estado_tramite", "inspector_asignado", "fecha_emision_permiso")
        and getattr(rodaje, k) != v
    }
    for key, value in update_data.items():
        setattr(rodaje, key, value)

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="Rodaje",
        resource_id=str(rodaje.id),
        details={
            "admin": True,
            "titular": rodaje.user_id,
            "campos": sorted(update_data.keys()),
            **({"cambios_clave": cambios_estado} if cambios_estado else {}),
        },
        request=request,
    )
    db.commit()
    db.refresh(rodaje)
    return rodaje


@rodaje_router.delete(
    "/admin/{rodaje_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Eliminar un rodaje",
)
async def admin_delete_rodaje(
    rodaje_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """[Admin] Eliminar cualquier rodaje"""
    check_permissions(db, current_user, "rodajes:manage")

    rodaje = db.query(Rodaje).filter(Rodaje.id == rodaje_id).first()
    if not rodaje:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    titulo, titular = rodaje.titulo_produccion, rodaje.user_id
    db.delete(rodaje)
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="Rodaje",
        resource_id=str(rodaje_id),
        details={"admin": True, "titular": titular, "titulo_produccion": titulo},
        request=request,
    )
    db.commit()
    return None


# === ESTADÍSTICAS ===


@rodaje_router.get("/admin/stats/resumen", summary="[Admin] Estadísticas de rodajes")
async def admin_stats_rodajes(
    anio: int = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    [Admin] Obtener estadísticas de rodajes.

    Retorna conteos por estado, tipo de producción y año.
    """
    check_permissions(db, current_user, "rodajes:manage")

    query = db.query(Rodaje)
    if anio:
        query = query.filter(Rodaje.anio_rodaje == anio)

    rodajes = query.all()

    # Conteo por estado
    estados = {}
    for r in rodajes:
        estado = r.estado_tramite or "sin_estado"
        estados[estado] = estados.get(estado, 0) + 1

    # Conteo por tipo de producción
    tipos = {}
    for r in rodajes:
        tipo = r.tipo_produccion or "sin_tipo"
        tipos[tipo] = tipos.get(tipo, 0) + 1

    # Conteo por año
    anios = {}
    for r in rodajes:
        a = r.anio_rodaje or "sin_anio"
        anios[a] = anios.get(a, 0) + 1

    return {
        "total": len(rodajes),
        "por_estado": estados,
        "por_tipo_produccion": tipos,
        "por_anio": anios,
    }
