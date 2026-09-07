"""
Rutas para el registro de Estudiantes del Sector Audiovisual (ESA).

Registro temporal (vigencia 1 año) para estudiantes que aún no están
inscriptos en el RePA principal. Permite acceder a beneficios y actividades
del IAAviM mientras completan su formación.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.crud_helpers import (
    apply_update_fields,
    check_duplicate_record,
    commit_or_conflict,
    delete_record,
    get_user_record,
    integrity_as_conflict,
)
from src.database import get_db
from src.models.esa_model import EstudianteESA
from src.schemas.esa_schemas import (
    EstudianteESACreate,
    EstudianteESAOut,
    EstudianteESAUpdate,
)
from src.services import lifecycle_service
from src.services.repa_code_service import generar_codigo_repa
from src.utils import get_current_user

esa_router = APIRouter()

# Mensajes de error reutilizables
MSG_NOT_FOUND = "No se encontró registro de Estudiante ESA"
MSG_DUPLICATE = "El usuario ya tiene un registro de Estudiante ESA"


@esa_router.post(
    "/",
    response_model=EstudianteESAOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro de Estudiante ESA",
    responses={
        201: {"description": "Registro creado exitosamente (vigencia 1 año)"},
        400: {"description": "El usuario ya tiene un registro ESA"},
        401: {"description": "No autenticado"},
    },
)
async def create_estudiante_esa(
    data: EstudianteESACreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Crear registro de Estudiante ESA para el usuario autenticado.

    El registro tiene **vigencia de 1 año** desde la fecha de alta.
    Requisitos: ser estudiante activo y no estar inscripto en el RePA principal.
    """
    check_duplicate_record(db, EstudianteESA, current_user["id"], MSG_DUPLICATE)

    # Calcular fecha de vencimiento (1 año)
    fecha_alta = datetime.now(timezone.utc)
    fecha_vencimiento = fecha_alta + timedelta(days=365)

    db_estudiante = EstudianteESA(
        **data.model_dump(),
        user_id=current_user["id"],
        fecha_alta=fecha_alta,
        fecha_vencimiento=fecha_vencimiento,
    )
    db.add(db_estudiante)
    with integrity_as_conflict(db):
        db.flush()
        lifecycle_service.procesar_actualizacion(db, db_estudiante, data.model_dump())
    commit_or_conflict(db)
    db.refresh(db_estudiante)
    return db_estudiante


@esa_router.get("/me", response_model=EstudianteESAOut)
async def get_my_estudiante_esa(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Obtener el registro de Estudiante ESA del usuario actual.

    Verifica la vigencia automáticamente: si fecha_vencimiento ya pasó,
    marca el registro como activo=False (baja momentánea).
    """
    estudiante = get_user_record(db, EstudianteESA, current_user["id"], MSG_NOT_FOUND)

    # Runtime vigencia check (fecha_vencimiento may be naive)
    now_utc = datetime.now(timezone.utc)
    venc = estudiante.fecha_vencimiento
    if venc and venc.tzinfo is None:
        venc = venc.replace(tzinfo=timezone.utc)
    if estudiante.activo and venc and venc < now_utc:
        estudiante.activo = False
        db.commit()
        db.refresh(estudiante)

    return estudiante


@esa_router.put("/me", response_model=EstudianteESAOut)
async def update_my_estudiante_esa(
    data: EstudianteESAUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar el registro de Estudiante ESA del usuario actual.

    Al enviar el formulario (borrador: false por primera vez) emite el
    código RePA propio del estudiante."""
    estudiante = get_user_record(db, EstudianteESA, current_user["id"], MSG_NOT_FOUND)
    update_data = apply_update_fields(estudiante, data)
    with integrity_as_conflict(db):
        lifecycle_service.procesar_actualizacion(db, estudiante, update_data)
    commit_or_conflict(db)
    db.refresh(estudiante)
    return estudiante


@esa_router.post("/me/renovar", response_model=EstudianteESAOut)
async def renovar_estudiante_esa(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Renovar el registro de Estudiante ESA por un año más.

    A diferencia de PF/PJ (código permanente), el código RePA de ESA vence
    junto con el registro: cada renovación emite un código NUEVO, no extiende
    el existente. Solo tiene sentido llamar a este endpoint si el estudiante
    ya envió el formulario alguna vez (si nunca lo hizo, no tiene código que
    renovar — usa el PUT /me para el primer envío)."""
    estudiante = get_user_record(db, EstudianteESA, current_user["id"], MSG_NOT_FOUND)

    # Renovar por un año desde hoy
    estudiante.fecha_vencimiento = datetime.now(timezone.utc) + timedelta(days=365)
    estudiante.activo = True
    estudiante.codigo_repa = generar_codigo_repa(db, EstudianteESA.REPA_TIPO)

    db.commit()
    db.refresh(estudiante)
    return estudiante


@esa_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_estudiante_esa(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Eliminar el registro de Estudiante ESA del usuario actual"""
    estudiante = get_user_record(db, EstudianteESA, current_user["id"], MSG_NOT_FOUND)
    delete_record(db, estudiante)
    return None
