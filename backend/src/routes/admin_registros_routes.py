# routes/admin_registros_routes.py
"""
Circuito de aprobación del Padrón RePA (Fase 3b).

Endpoints admin genéricos, parametrizados por tipo de registro (pf, pj, as,
esa, agam), para:
- listar/buscar el padrón completo (backoffice)
- ver el detalle de un registro de cualquier usuario
- aprobar / observar / rechazar, invocando lifecycle_service (ya escrito en
  Fase 3a) y dejando auditoría de cada acción.

El envío del formulario deja el registro en estado "enviado" (Fase 3a, el
código RePA ya se emitió ahí). Estos endpoints lo toman para revisión
automáticamente si hace falta antes de aplicar la acción — no exponen un
paso separado de "tomar para revisión" en la UI, alcanza con aprobar/
observar/rechazar directamente sobre un registro "enviado".
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.audit import audit_log
from src.database import get_db
from src.models.asociacion_model import Asociacion
from src.models.audit_model import AuditAction
from src.models.esa_model import EstudianteESA
from src.models.obra_audiovisual_model import ObraAudiovisual
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica
from src.models.registro_lifecycle import EstadoRegistro
from src.models.user_models import User
from src.schemas.asociacion_schemas import AsociacionOut
from src.schemas.esa_schemas import EstudianteESAOut
from src.schemas.obra_audiovisual_schemas import ObraAudiovisualOut
from src.schemas.persona_fisica_schemas import PersonaFisicaOut
from src.schemas.persona_juridica_schemas import PersonaJuridicaOut
from src.search import filtro_texto
from src.services import lifecycle_service
from src.utils import require_permissions

admin_registros_router = APIRouter(prefix="/admin/registros", tags=["admin-registros"])

# tipo (path param) -> (modelo SQLAlchemy, schema de salida, campos de búsqueda de texto)
_TIPOS = {
    "pf": (
        PersonaFisica,
        PersonaFisicaOut,
        [
            PersonaFisica.nombre,
            PersonaFisica.apellido,
            PersonaFisica.dni,
            PersonaFisica.email,
        ],
    ),
    "pj": (
        PersonaJuridica,
        PersonaJuridicaOut,
        [PersonaJuridica.nombre_pj, PersonaJuridica.cuit],
    ),
    "as": (Asociacion, AsociacionOut, [Asociacion.nombre_asociacion, Asociacion.cuit]),
    "esa": (
        EstudianteESA,
        EstudianteESAOut,
        [EstudianteESA.nombre_completo, EstudianteESA.dni],
    ),
    "agam": (ObraAudiovisual, ObraAudiovisualOut, [ObraAudiovisual.titulo]),
}


def _resolve_tipo(tipo: str):
    entry = _TIPOS.get(tipo.lower())
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de registro inválido: {tipo!r}. Válidos: {', '.join(_TIPOS)}",
        )
    return entry


# Etiqueta legible y resolución de "nombre" / "código" por tipo, para la vista
# unificada del padrón. Cada formulario nombra distinto a su titular, y AS/AGAM
# no emiten código propio: heredan el de la Persona Física que los presenta.
_ETIQUETA_TIPO = {
    "pf": "Persona Física",
    "pj": "Persona Jurídica",
    "as": "Asociación / Colectivo",
    "esa": "Estudiante ESA",
    "agam": "Obra Audiovisual",
}


def _nombre_de(tipo: str, r) -> str:
    if tipo == "pf":
        return f"{r.nombre or ''} {r.apellido or ''}".strip() or "(sin nombre)"
    if tipo == "pj":
        return r.nombre_pj or "(sin nombre)"
    if tipo == "as":
        return r.nombre_asociacion or "(sin nombre)"
    if tipo == "esa":
        return r.nombre_completo or "(sin nombre)"
    return r.titulo or "(sin título)"


def _codigo_de(r) -> str | None:
    # AS y AGAM usan `codigo_repa_titular` como código de trámite.
    return getattr(r, "codigo_repa", None) or getattr(r, "codigo_repa_titular", None)


def _get_registro_or_404(db: Session, model, registro_id: int):
    registro = db.query(model).filter(model.id == registro_id).first()
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )
    return registro


def _asegurar_en_revision(db: Session, registro) -> None:
    """Las acciones de revisión (aprobar/observar/rechazar) requieren estado
    'en_revision'. El envío deja el registro en 'enviado' — lo toma para
    revisión automáticamente si hace falta, para no exigir un paso extra en
    la UI del revisor."""
    if registro.estado == EstadoRegistro.enviado.value:
        lifecycle_service.tomar_para_revision(db, registro)


class AccionRevisionBody(BaseModel):
    motivo: str | None = None


@admin_registros_router.get(
    "", summary="[Admin] Padrón unificado: todos los tipos en una sola lista"
)
async def listar_registros_unificado(
    tipos: list[str] | None = Query(
        None, description="Tipos a incluir (pf, pj, as, esa, agam). Vacío = todos."
    ),
    estados: list[str] | None = Query(
        None, description="Estados a incluir (multi-selección). Vacío = todos."
    ),
    incluir_borradores: bool = Query(
        False,
        description=(
            "Por defecto los borradores NO se muestran: el usuario todavía no los "
            "envió, así que no hay nada que revisar. True los incluye (soporte)."
        ),
    ),
    q: str | None = Query(None, description="Búsqueda de texto libre (ignora acentos)"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("registros:read_all")),
):
    """Vista unificada del padrón: mezcla los 5 tipos en una sola lista ordenada.

    Los 5 formularios viven en tablas distintas con columnas distintas, así que en
    vez de un UNION SQL sobre modelos heterogéneos se consulta cada tabla con los
    mismos filtros y se mezcla en Python, proyectando una forma común. Es más
    simple y robusto; el padrón provincial tiene un volumen que lo permite.
    """
    seleccion = [t.lower() for t in (tipos or _TIPOS.keys()) if t.lower() in _TIPOS]
    if not seleccion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ningún tipo válido. Válidos: {', '.join(_TIPOS)}",
        )

    filas: list[dict] = []
    for tipo in seleccion:
        model, _schema, campos_busqueda = _TIPOS[tipo]
        query = db.query(model)
        if estados:
            query = query.filter(model.estado.in_(estados))
        if not incluir_borradores:
            query = query.filter(model.borrador.is_(False))
        if q and q.strip() and campos_busqueda:
            query = query.filter(filtro_texto(db, campos_busqueda, q.strip()))

        for r in query.all():
            filas.append(
                {
                    "tipo": tipo,
                    "tipo_label": _ETIQUETA_TIPO[tipo],
                    "id": r.id,
                    "nombre": _nombre_de(tipo, r),
                    "estado": r.estado,
                    "borrador": r.borrador,
                    "codigo_repa": _codigo_de(r),
                    "updated_at": r.updated_at,
                    "user_id": r.user_id,
                }
            )

    # Más recientes primero; los que no tienen fecha van al final.
    filas.sort(
        key=lambda f: (f["updated_at"] is not None, f["updated_at"]), reverse=True
    )
    total = len(filas)
    pagina = filas[offset : offset + limit]

    # Email del titular: una sola consulta para toda la página (evita N+1).
    user_ids = {f["user_id"] for f in pagina if f["user_id"]}
    if user_ids:
        emails = dict(db.query(User.id, User.email).filter(User.id.in_(user_ids)).all())
        for f in pagina:
            f["user_email"] = emails.get(f["user_id"])
    else:
        for f in pagina:
            f["user_email"] = None

    return {"items": pagina, "total": total, "offset": offset, "limit": limit}


@admin_registros_router.get(
    "/{tipo}", summary="[Admin] Padrón: listar/buscar registros por tipo"
)
async def listar_registros(
    tipo: str,
    estado: str | None = Query(
        None, description="Filtrar por estado del ciclo de vida"
    ),
    borrador: bool | None = Query(None, description="Filtrar por borrador"),
    q: str | None = Query(None, description="Búsqueda de texto libre"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("registros:read_all")),
):
    model, schema, campos_busqueda = _resolve_tipo(tipo)
    query = db.query(model)
    if estado:
        query = query.filter(model.estado == estado)
    if borrador is not None:
        query = query.filter(model.borrador == borrador)
    if q and q.strip() and campos_busqueda:
        query = query.filter(filtro_texto(db, campos_busqueda, q.strip()))

    total = query.count()
    registros = query.order_by(model.id.desc()).offset(offset).limit(limit).all()
    return {
        "items": [schema.model_validate(r) for r in registros],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@admin_registros_router.get(
    "/{tipo}/{registro_id}", summary="[Admin] Ver el detalle de un registro"
)
async def obtener_registro(
    tipo: str,
    registro_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_permissions("registros:read_all")),
):
    model, schema, _campos = _resolve_tipo(tipo)
    registro = _get_registro_or_404(db, model, registro_id)
    return schema.model_validate(registro)


@admin_registros_router.post(
    "/{tipo}/{registro_id}/aprobar", summary="[Admin] Aprobar un registro"
)
async def aprobar_registro(
    tipo: str,
    registro_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("registros:revisar")),
):
    model, schema, _campos = _resolve_tipo(tipo)
    registro = _get_registro_or_404(db, model, registro_id)
    try:
        _asegurar_en_revision(db, registro)
        codigo = lifecycle_service.aprobar(db, registro, revisor_id=current_user["id"])
    except lifecycle_service.TransicionInvalida as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type=model.__name__,
        resource_id=str(registro.id),
        details={
            "accion": "aprobar",
            "codigo_repa": codigo,
            "titular": registro.user_id,
        },
        request=request,
    )
    db.commit()
    db.refresh(registro)
    return schema.model_validate(registro)


@admin_registros_router.post(
    "/{tipo}/{registro_id}/observar",
    summary="[Admin] Observar un registro (vuelve al usuario)",
)
async def observar_registro(
    tipo: str,
    registro_id: int,
    body: AccionRevisionBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("registros:revisar")),
):
    if not body.motivo or not body.motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El motivo de la observación es obligatorio",
        )
    model, schema, _campos = _resolve_tipo(tipo)
    registro = _get_registro_or_404(db, model, registro_id)
    try:
        _asegurar_en_revision(db, registro)
        lifecycle_service.observar(
            db, registro, motivo=body.motivo, revisor_id=current_user["id"]
        )
    except lifecycle_service.TransicionInvalida as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type=model.__name__,
        resource_id=str(registro.id),
        details={
            "accion": "observar",
            "motivo": body.motivo,
            "titular": registro.user_id,
        },
        request=request,
    )
    db.commit()
    db.refresh(registro)
    return schema.model_validate(registro)


@admin_registros_router.post(
    "/{tipo}/{registro_id}/rechazar", summary="[Admin] Rechazar un registro (terminal)"
)
async def rechazar_registro(
    tipo: str,
    registro_id: int,
    body: AccionRevisionBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permissions("registros:revisar")),
):
    if not body.motivo or not body.motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El motivo del rechazo es obligatorio",
        )
    model, schema, _campos = _resolve_tipo(tipo)
    registro = _get_registro_or_404(db, model, registro_id)
    try:
        _asegurar_en_revision(db, registro)
        lifecycle_service.rechazar(
            db, registro, motivo=body.motivo, revisor_id=current_user["id"]
        )
    except lifecycle_service.TransicionInvalida as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    audit_log(
        db=db,
        action=AuditAction.UPDATE,
        user_id=current_user["id"],
        resource_type=model.__name__,
        resource_id=str(registro.id),
        details={
            "accion": "rechazar",
            "motivo": body.motivo,
            "titular": registro.user_id,
        },
        request=request,
    )
    db.commit()
    db.refresh(registro)
    return schema.model_validate(registro)
