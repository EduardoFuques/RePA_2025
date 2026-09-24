"""
Rutas del modulo de Expedientes Administrativos (Administracion General).

Registra y hace trazable la ejecucion presupuestaria del IAAviM: expedientes,
montos, resolucion asociada y estado de pago.

Es un backoffice de uso interno del area: TODOS los endpoints exigen el
permiso "expedientes:manage". No hay variante "mis expedientes" porque el
expediente no pertenece a quien lo carga sino al area solicitante.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from src.audit import audit_log
from src.database import get_db
from src.models.audit_model import AuditAction
from src.models.expediente_model import ExpedienteAdministrativo
from src.routes.upload_routes import servir_adjunto_de_area
from src.schemas.expediente_schemas import (
    ExpedienteCreate,
    ExpedienteListOut,
    ExpedienteOut,
    ExpedienteResumenOut,
    ExpedienteUpdate,
)
from src.utils import check_permissions, get_current_user

expediente_router = APIRouter()

MSG_NOT_FOUND = "No se encontró el expediente administrativo"

# Un solo permiso para todo el modulo: el area que carga expedientes es la
# misma que los consulta y los cierra, no hay separacion de lectura/escritura.
PERM_EXPEDIENTES = "expedientes:manage"


def _get_expediente_or_404(db: Session, expediente_id: int):
    """Busca el expediente o corta con 404 (evita repetir el patron en cada handler)."""
    expediente = (
        db.query(ExpedienteAdministrativo)
        .filter(ExpedienteAdministrativo.id == expediente_id)
        .first()
    )
    if not expediente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND
        )
    return expediente


@expediente_router.post(
    "/",
    response_model=ExpedienteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un expediente administrativo",
    responses={
        201: {"description": "Expediente creado"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permiso expedientes:manage"},
    },
)
async def crear_expediente(
    data: ExpedienteCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear un expediente administrativo.

    El identificador del expediente es el `id` incremental que devuelve este
    endpoint. `numero_expediente_provincial` es un campo libre opcional: en
    esta version no hay integracion con el sistema provincial.
    """
    check_permissions(db, current_user, PERM_EXPEDIENTES)

    expediente = ExpedienteAdministrativo(**data.model_dump())
    db.add(expediente)
    # flush y no commit: necesitamos el id autogenerado para la auditoria, pero
    # queremos que expediente y AuditLog entren en la misma transaccion.
    db.flush()
    audit_log(
        db=db,
        action=AuditAction.CREATE,
        user_id=current_user["id"],
        resource_type="ExpedienteAdministrativo",
        resource_id=str(expediente.id),
        details={
            "area_solicitante": expediente.area_solicitante,
            "tipo_expediente": expediente.tipo_expediente,
            "monto_solicitado": expediente.monto_solicitado,
        },
        request=request,
    )
    db.commit()
    db.refresh(expediente)
    return expediente


@expediente_router.get(
    "/",
    response_model=ExpedienteListOut,
    summary="Listar expedientes administrativos (paginado)",
)
async def listar_expedientes(
    request: Request,
    estado: str | None = Query(None, description="Filtra por estado_expediente"),
    area: str | None = Query(None, description="Filtra por area_solicitante"),
    anio: int | None = Query(None, description="Año de fecha_alta"),
    tipo_expediente: str | None = Query(None, description="Filtra por tipo"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listar expedientes con filtros y paginacion.

    `total` es el total que matchea los filtros (no el de la pagina), para que
    el frontend pueda dibujar el paginador sin pedir todo el conjunto.
    """
    check_permissions(db, current_user, PERM_EXPEDIENTES)

    query = db.query(ExpedienteAdministrativo)
    if estado:
        query = query.filter(ExpedienteAdministrativo.estado_expediente == estado)
    if area:
        query = query.filter(ExpedienteAdministrativo.area_solicitante == area)
    if tipo_expediente:
        query = query.filter(
            ExpedienteAdministrativo.tipo_expediente == tipo_expediente
        )
    if anio is not None:
        # extract en SQL y no filtro por rango de fechas en Python: el año se
        # resuelve en la base y no obliga a traer todas las filas.
        query = query.filter(
            extract("year", ExpedienteAdministrativo.fecha_alta) == anio
        )

    total = query.count()
    items = (
        query.order_by(ExpedienteAdministrativo.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@expediente_router.get(
    "/stats/resumen",
    response_model=ExpedienteResumenOut,
    summary="Indicadores de ejecución presupuestaria",
)
async def resumen_expedientes(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Indicadores pedidos por el formulario del area:

    - porcentaje de ejecucion presupuestaria por area y por año;
    - cantidad y monto por tipo de expediente.

    Todo se calcula con agregaciones en SQL (una consulta por indicador): el
    volumen de expedientes crece por año y no tiene sentido traerlos a memoria.
    """
    check_permissions(db, current_user, PERM_EXPEDIENTES)

    anio_col = extract("year", ExpedienteAdministrativo.fecha_alta).label("anio")
    filas_area = (
        db.query(
            ExpedienteAdministrativo.area_solicitante,
            anio_col,
            func.coalesce(func.sum(ExpedienteAdministrativo.monto_aprobado), 0).label(
                "aprobado"
            ),
            func.coalesce(func.sum(ExpedienteAdministrativo.monto_ejecutado), 0).label(
                "ejecutado"
            ),
        )
        .group_by(ExpedienteAdministrativo.area_solicitante, anio_col)
        .order_by(anio_col, ExpedienteAdministrativo.area_solicitante)
        .all()
    )

    ejecucion_por_area_anio = []
    for area, anio, aprobado, ejecutado in filas_area:
        # El porcentaje se arma en Python y no en SQL para poder distinguir
        # "0% ejecutado" de "sin presupuesto aprobado" (None).
        porcentaje = (
            round(float(ejecutado) / float(aprobado) * 100, 2)
            if aprobado and float(aprobado) != 0
            else None
        )
        ejecucion_por_area_anio.append(
            {
                "area_solicitante": area,
                "anio": int(anio) if anio is not None else None,
                "monto_aprobado": aprobado,
                "monto_ejecutado": ejecutado,
                "porcentaje_ejecucion": porcentaje,
            }
        )

    filas_tipo = (
        db.query(
            ExpedienteAdministrativo.tipo_expediente,
            func.count(ExpedienteAdministrativo.id).label("cantidad"),
            func.coalesce(func.sum(ExpedienteAdministrativo.monto_solicitado), 0),
            func.coalesce(func.sum(ExpedienteAdministrativo.monto_aprobado), 0),
            func.coalesce(func.sum(ExpedienteAdministrativo.monto_ejecutado), 0),
        )
        .group_by(ExpedienteAdministrativo.tipo_expediente)
        .order_by(ExpedienteAdministrativo.tipo_expediente)
        .all()
    )
    por_tipo_expediente = [
        {
            "tipo_expediente": tipo,
            "cantidad": cantidad,
            "monto_solicitado": solicitado,
            "monto_aprobado": aprobado,
            "monto_ejecutado": ejecutado,
        }
        for tipo, cantidad, solicitado, aprobado, ejecutado in filas_tipo
    ]

    return {
        "ejecucion_por_area_anio": ejecucion_por_area_anio,
        "por_tipo_expediente": por_tipo_expediente,
    }


@expediente_router.get(
    "/{expediente_id}",
    response_model=ExpedienteOut,
    summary="Obtener un expediente por ID",
)
async def obtener_expediente(
    expediente_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener un expediente administrativo por su ID interno."""
    check_permissions(db, current_user, PERM_EXPEDIENTES)
    return _get_expediente_or_404(db, expediente_id)


@expediente_router.get(
    "/{expediente_id}/resolucion-pdf",
    summary="Descargar el PDF de la resolución del expediente",
)
async def descargar_resolucion_pdf(
    expediente_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """El PDF lo sube un gestor y lo abre cualquiera del area; queda auditado
    igual que las descargas de adjuntos del padron."""
    check_permissions(db, current_user, PERM_EXPEDIENTES)
    expediente = _get_expediente_or_404(db, expediente_id)
    respuesta = servir_adjunto_de_area(
        expediente.resolucion_pdf_path, "expediente_resolucion"
    )
    audit_log(
        db=db,
        action=AuditAction.DOCUMENTO_DESCARGADO,
        user_id=current_user["id"],
        resource_type="ExpedienteAdministrativo",
        resource_id=str(expediente_id),
        details={"adjunto": "resolucion_pdf_path"},
        request=request,
    )
    db.commit()
    return respuesta


@expediente_router.put(
    "/{expediente_id}",
    response_model=ExpedienteOut,
    summary="Actualizar un expediente",
)
async def actualizar_expediente(
    expediente_id: int,
    data: ExpedienteUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar un expediente administrativo.

    Actualizacion parcial: solo se tocan los campos presentes en el body
    (exclude_unset), asi avanzar el estado del expediente no borra los montos
    ya cargados.
    """
    check_permissions(db, current_user, PERM_EXPEDIENTES)
    expediente = _get_expediente_or_404(db, expediente_id)

    update_data = data.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(expediente, campo, valor)

    db.flush()
    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="ExpedienteAdministrativo",
        resource_id=str(expediente.id),
        # Solo los nombres de campo: el detalle completo esta en la fila.
        details={"campos": sorted(update_data.keys())},
        request=request,
    )
    db.commit()
    db.refresh(expediente)
    return expediente


@expediente_router.delete(
    "/{expediente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un expediente",
)
async def eliminar_expediente(
    expediente_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un expediente administrativo — SOLO si es un borrador.

    El formulario del area no preve borrar (hace "trazable la ejecucion
    presupuestaria" y los indicadores se calculan sobre la historia). Lo
    unico que se puede eliminar es una carga a medio hacer: el autoguardado
    crea el borrador con el primer campo, y uno abandonado no tiene por que
    quedar para siempre en el listado. Uno ya cargado sigue su ciclo por
    estado_expediente (hasta "observado_rechazado"), no se borra: 409.
    """
    check_permissions(db, current_user, PERM_EXPEDIENTES)
    expediente = _get_expediente_or_404(db, expediente_id)
    if not expediente.borrador:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Un expediente ya cargado no se elimina: queda en el historial "
                "de ejecución presupuestaria. Solo se pueden eliminar borradores."
            ),
        )

    # La auditoria se emite ANTES del delete: despues del db.delete() los
    # atributos del objeto ya no son legibles para armar el detalle.
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="ExpedienteAdministrativo",
        resource_id=str(expediente.id),
        details={
            "area_solicitante": expediente.area_solicitante,
            "numero_expediente_provincial": expediente.numero_expediente_provincial,
        },
        request=request,
    )
    db.delete(expediente)
    db.commit()
    return None
