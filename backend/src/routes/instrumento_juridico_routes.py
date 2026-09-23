"""
Rutas del Digesto Jurídico Institucional (Área de Asuntos Jurídicos - IAAviM).

Módulo de uso interno del área: TODOS los endpoints exigen el permiso
"instrumentos:manage". No hay rutas /me ni ownership por usuario — el digesto es
un archivo institucional único, no un trámite de un solicitante.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import String as SAString
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from src.audit import audit_log
from src.database import get_db
from src.models.audit_model import AuditAction
from src.models.instrumento_juridico_model import (
    ActaConsejoDirectivo,
    InstrumentoJuridico,
)
from src.schemas.instrumento_juridico_schemas import (
    InstrumentoCreate,
    InstrumentoListOut,
    InstrumentoOut,
    InstrumentoUpdate,
)
from src.utils import check_permissions, get_current_user

instrumento_juridico_router = APIRouter()

MSG_NOT_FOUND = "No se encontró el instrumento jurídico"

# Tipo de documento que habilita el bloque condicional de la sección 4.
TIPO_ACTA_CONSEJO = "acta_consejo_directivo"

# Tipos que cuentan como "convenio" para el informe de convenios vigentes.
TIPOS_CONVENIO = ("convenio_aporte", "convenio_marco")


def _filtro_lista_json(columna, valor: str):
    """
    Filtra una columna JSON que guarda una lista de strings.

    Se castea a texto y se busca el valor entrecomillado en vez de usar el
    operador de contención: la columna es JSON (no JSONB) y JSON no soporta
    `@>` en PostgreSQL. Las comillas evitan que "repa" matchee "repa_extendido".
    """
    return func.cast(columna, SAString).ilike(f'%"{valor}"%')


def _aplicar_acta(db: Session, instrumento: InstrumentoJuridico, acta_data) -> None:
    """
    Crea o actualiza (upsert) el acta 1:1 del instrumento.

    El acta solo se guarda si el tipo de documento la habilita; si el tipo
    cambió y ya no es un acta del Consejo, no se toca lo existente acá (eso lo
    resuelve explícitamente el endpoint de update).
    """
    payload = acta_data.model_dump()
    asistentes = payload.get("asistentes")
    if asistentes:
        # Los asistentes llegan como modelos Pydantic anidados: hay que
        # serializarlos a dict para que entren en la columna JSON.
        payload["asistentes"] = [
            a.model_dump() if hasattr(a, "model_dump") else a for a in asistentes
        ]

    if instrumento.acta is None:
        instrumento.acta = ActaConsejoDirectivo(**payload)
    else:
        for key, value in payload.items():
            setattr(instrumento.acta, key, value)
    db.flush()


def _validar_acta_permitida(tipo_documento: str | None, acta_data) -> None:
    """El bloque de acta es condicional: si el tipo no lo habilita, es un 400."""
    if acta_data is not None and tipo_documento != TIPO_ACTA_CONSEJO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El bloque de acta solo aplica cuando tipo_documento es "
                f"'{TIPO_ACTA_CONSEJO}'"
            ),
        )


# === CRUD DEL DIGESTO ===


@instrumento_juridico_router.post(
    "/",
    response_model=InstrumentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un instrumento jurídico",
    responses={
        201: {"description": "Instrumento registrado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Sin permiso instrumentos:manage"},
    },
)
async def create_instrumento(
    data: InstrumentoCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Registrar un instrumento legal en el digesto jurídico institucional.

    Si el tipo de documento es 'acta_consejo_directivo' se puede enviar el
    bloque `acta`, que se persiste en la tabla actas_consejo_directivo.
    """
    check_permissions(db, current_user, "instrumentos:manage")

    payload = data.model_dump(exclude={"acta"})
    _validar_acta_permitida(data.tipo_documento, data.acta)

    # estado_revision arranca en "en_revision" salvo que el área lo fije.
    if payload.get("estado_revision") is None:
        payload["estado_revision"] = "en_revision"

    instrumento = InstrumentoJuridico(**payload, usuario_carga_id=current_user["id"])
    db.add(instrumento)
    db.flush()

    if data.acta is not None:
        _aplicar_acta(db, instrumento, data.acta)

    audit_log(
        db=db,
        action=AuditAction.CREATE,
        user_id=current_user["id"],
        resource_type="InstrumentoJuridico",
        resource_id=str(instrumento.id),
        details={
            "tipo_documento": data.tipo_documento,
            "numero_instrumento": data.numero_instrumento,
            "con_acta": data.acta is not None,
        },
        request=request,
    )
    db.commit()
    db.refresh(instrumento)
    return instrumento


@instrumento_juridico_router.get(
    "/",
    summary="Listar y buscar instrumentos jurídicos",
    responses={200: {"description": "Página de resultados del digesto"}},
)
async def list_instrumentos(
    tipo_documento: str | None = Query(None, description="Tipo de documento"),
    numero_instrumento: str | None = Query(
        None, description="Número o código interno (coincidencia parcial)"
    ),
    anio: int | None = Query(None, description="Año de la fecha de emisión"),
    area_vinculada: str | None = Query(
        None, description="Área o gerencia vinculada (una de la lista)"
    ),
    tematica_principal: str | None = Query(None, description="Temática principal"),
    ambito_aplicacion: str | None = Query(None, description="Ámbito de aplicación"),
    estado_revision: str | None = Query(None, description="Estado de revisión"),
    vigente: bool | None = Query(
        None, description="True: vigentes hoy. False: vencidos o aún no vigentes"
    ),
    q: str | None = Query(
        None, description="Texto libre: palabras clave, título o resumen"
    ),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Listado paginado del digesto con los filtros que pide el formulario:
    tipo, número, año, área vinculada, temática, palabras clave, ámbito y vigencia.
    """
    check_permissions(db, current_user, "instrumentos:manage")

    query = db.query(InstrumentoJuridico)

    if tipo_documento:
        query = query.filter(InstrumentoJuridico.tipo_documento == tipo_documento)
    if numero_instrumento:
        query = query.filter(
            InstrumentoJuridico.numero_instrumento.ilike(f"%{numero_instrumento}%")
        )
    if anio:
        query = query.filter(extract("year", InstrumentoJuridico.fecha_emision) == anio)
    if area_vinculada:
        query = query.filter(
            _filtro_lista_json(InstrumentoJuridico.areas_vinculadas, area_vinculada)
        )
    if tematica_principal:
        query = query.filter(
            InstrumentoJuridico.tematica_principal == tematica_principal
        )
    if ambito_aplicacion:
        query = query.filter(
            InstrumentoJuridico.ambito_aplicacion == ambito_aplicacion
        )
    if estado_revision:
        query = query.filter(InstrumentoJuridico.estado_revision == estado_revision)
    if vigente is not None:
        hoy = date.today()
        # Vigente = ya empezó (o no declara inicio) y todavía no expiró
        # (o no declara expiración: los convenios marco suelen no tenerla).
        cond_vigente = (
            or_(
                InstrumentoJuridico.fecha_inicio_vigencia.is_(None),
                InstrumentoJuridico.fecha_inicio_vigencia <= hoy,
            )
        ) & (
            or_(
                InstrumentoJuridico.fecha_expiracion.is_(None),
                InstrumentoJuridico.fecha_expiracion >= hoy,
            )
        )
        query = query.filter(cond_vigente if vigente else ~cond_vigente)
    if q and q.strip():
        patron = f"%{q.strip()}%"
        query = query.filter(
            or_(
                InstrumentoJuridico.titulo.ilike(patron),
                InstrumentoJuridico.resumen.ilike(patron),
                func.cast(InstrumentoJuridico.palabras_clave, SAString).ilike(patron),
            )
        )

    total = query.count()
    registros = (
        query.order_by(InstrumentoJuridico.id.desc()).offset(offset).limit(limit).all()
    )
    return {
        "items": [InstrumentoListOut.model_validate(r) for r in registros],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


# === INFORMES ===
# Va ANTES de /{instrumento_id} a propósito: si se declarara después, FastAPI
# igual resolvería bien por el tipo int del path param, pero el orden explícito
# evita sorpresas si alguien cambia el tipo del parámetro.


@instrumento_juridico_router.get(
    "/admin/stats/resumen",
    summary="[Admin] Informes del digesto jurídico",
)
async def admin_stats_resumen(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Informes que pide el doc: volumen de instrumentos por año, por área
    vinculada y cantidad de convenios vigentes.
    """
    check_permissions(db, current_user, "instrumentos:manage")

    total = db.query(func.count(InstrumentoJuridico.id)).scalar() or 0

    # Volumen por año de emisión (agregación en SQL).
    filas_anio = (
        db.query(
            extract("year", InstrumentoJuridico.fecha_emision).label("anio"),
            func.count(InstrumentoJuridico.id),
        )
        .group_by("anio")
        .all()
    )
    por_anio = {
        (str(int(anio)) if anio is not None else "sin_anio"): cantidad
        for anio, cantidad in filas_anio
    }

    # Volumen por área: areas_vinculadas es una lista JSON, así que el conteo
    # se hace en Python (desanidar un JSON en SQL portable no vale la pena para
    # un catálogo de 11 áreas).
    por_area: dict[str, int] = {}
    for (areas,) in db.query(InstrumentoJuridico.areas_vinculadas).all():
        for area in areas or []:
            por_area[area] = por_area.get(area, 0) + 1

    hoy = date.today()
    convenios_vigentes = (
        db.query(func.count(InstrumentoJuridico.id))
        .filter(
            InstrumentoJuridico.tipo_documento.in_(TIPOS_CONVENIO),
            or_(
                InstrumentoJuridico.fecha_inicio_vigencia.is_(None),
                InstrumentoJuridico.fecha_inicio_vigencia <= hoy,
            ),
            or_(
                InstrumentoJuridico.fecha_expiracion.is_(None),
                InstrumentoJuridico.fecha_expiracion >= hoy,
            ),
        )
        .scalar()
        or 0
    )

    return {
        "total": total,
        "por_anio": por_anio,
        "por_area": por_area,
        "convenios_vigentes": convenios_vigentes,
    }


@instrumento_juridico_router.get(
    "/{instrumento_id}",
    response_model=InstrumentoOut,
    summary="Obtener un instrumento jurídico",
)
async def get_instrumento(
    instrumento_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener el detalle de un instrumento, con su acta si corresponde."""
    check_permissions(db, current_user, "instrumentos:manage")

    instrumento = (
        db.query(InstrumentoJuridico)
        .filter(InstrumentoJuridico.id == instrumento_id)
        .first()
    )
    if not instrumento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    return instrumento


@instrumento_juridico_router.put(
    "/{instrumento_id}",
    response_model=InstrumentoOut,
    summary="Actualizar un instrumento jurídico",
)
async def update_instrumento(
    instrumento_id: int,
    data: InstrumentoUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Actualizar un instrumento del digesto.

    Todo cambio queda en el audit_log: ese es el "historial de modificaciones"
    que pide la sección 7, sin tabla de log propia.
    """
    check_permissions(db, current_user, "instrumentos:manage")

    instrumento = (
        db.query(InstrumentoJuridico)
        .filter(InstrumentoJuridico.id == instrumento_id)
        .first()
    )
    if not instrumento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    update_data = data.model_dump(exclude_unset=True, exclude={"acta"})

    # El tipo resultante manda sobre la validez del bloque de acta: puede venir
    # en el mismo PUT que cambia tipo_documento.
    tipo_resultante = update_data.get("tipo_documento", instrumento.tipo_documento)
    _validar_acta_permitida(tipo_resultante, data.acta)

    for key, value in update_data.items():
        setattr(instrumento, key, value)

    if data.acta is not None:
        _aplicar_acta(db, instrumento, data.acta)

    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type="InstrumentoJuridico",
        resource_id=str(instrumento.id),
        details={
            "campos": sorted(update_data.keys()),
            "acta_modificada": data.acta is not None,
        },
        request=request,
    )
    db.commit()
    db.refresh(instrumento)
    return instrumento


@instrumento_juridico_router.delete(
    "/{instrumento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un instrumento jurídico",
)
async def delete_instrumento(
    instrumento_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eliminar un instrumento. El acta asociada se borra en cascada."""
    check_permissions(db, current_user, "instrumentos:manage")

    instrumento = (
        db.query(InstrumentoJuridico)
        .filter(InstrumentoJuridico.id == instrumento_id)
        .first()
    )
    if not instrumento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NOT_FOUND)

    tipo, numero = instrumento.tipo_documento, instrumento.numero_instrumento
    db.delete(instrumento)
    audit_log(
        db=db,
        action=AuditAction.DELETE,
        user_id=current_user["id"],
        resource_type="InstrumentoJuridico",
        resource_id=str(instrumento_id),
        details={"tipo_documento": tipo, "numero_instrumento": numero},
        request=request,
    )
    db.commit()
    return None
