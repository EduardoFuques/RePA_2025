# services/fomento_relational_service.py
"""Sincronización de las relaciones 1:N de Fomento que antes vivían como JSON
suelto: `TramiteFomento.pagos`/`otros_aportes_no_iaavim` y
`ComiteFomento.integrantes`.

Patrón "reemplazar todo al guardar": el caller sigue mandando la lista
completa en cada guardado (igual que hoy manda el JSON completo) — acá
adentro se borran las filas hijas existentes y se reinsertan desde la lista
recibida. No es un diff incremental porque el frontend no trackea IDs por
fila; reemplazar-todo es simple de razonar (después de esta llamada, las
filas hijas son EXACTAMENTE lo que se mandó) y evita rediseñar la UI.

`sync_integrantes` valida TODOS los `evaluador_id` contra la tabla
`evaluadores` ANTES de tocar una sola fila — si alguno no existe, se
rechaza el lote completo (nada se aplica parcialmente).
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.fomento_model import (
    AporteFomento,
    ComiteFomento,
    Evaluador,
    IntegranteComite,
    PagoFomento,
    TramiteFomento,
)
from src.schemas.fomento_schemas import AporteItem, IntegranteItem, PagoItem


def sync_pagos(db: Session, tramite: TramiteFomento, items: list[PagoItem] | None) -> None:
    """Reemplaza todos los pagos del trámite por `items`. No-op si `items`
    es None (campo ausente del payload — no tocar lo existente)."""
    if items is None:
        return
    db.query(PagoFomento).filter(PagoFomento.tramite_id == tramite.id).delete()
    db.flush()
    for item in items:
        db.add(PagoFomento(tramite_id=tramite.id, **item.model_dump()))


def sync_aportes(db: Session, tramite: TramiteFomento, items: list[AporteItem] | None) -> None:
    """Reemplaza todos los aportes del trámite por `items`. No-op si `items`
    es None (campo ausente del payload — no tocar lo existente)."""
    if items is None:
        return
    db.query(AporteFomento).filter(AporteFomento.tramite_id == tramite.id).delete()
    db.flush()
    for item in items:
        db.add(AporteFomento(tramite_id=tramite.id, **item.model_dump()))


def sync_integrantes(
    db: Session, comite: ComiteFomento, items: list[IntegranteItem] | None
) -> None:
    """Reemplaza todos los integrantes del comité por `items`. No-op si
    `items` es None. Valida que todos los evaluador_id existan ANTES de
    borrar/insertar nada — rechaza el lote completo (404) si alguno no
    existe, sin aplicar parcialmente."""
    if items is None:
        return
    if items:
        ids = {item.evaluador_id for item in items}
        encontrados = {
            row[0]
            for row in db.query(Evaluador.id).filter(Evaluador.id.in_(ids)).all()
        }
        faltantes = ids - encontrados
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluador(es) no encontrado(s): {sorted(faltantes)}",
            )
    db.query(IntegranteComite).filter(IntegranteComite.comite_id == comite.id).delete()
    db.flush()
    for item in items:
        db.add(IntegranteComite(comite_id=comite.id, **item.model_dump()))


def attach_output_fields(tramite: TramiteFomento) -> TramiteFomento:
    """Adjunta `pagos`/`otros_aportes_no_iaavim` como atributos planos
    (listas de schema, no columnas ORM) para que `TramiteFomentoOut` los
    lea vía from_attributes, igual que antes cuando eran columnas JSON."""
    tramite.pagos = [PagoItem.model_validate(p) for p in tramite.pagos_rel]
    tramite.otros_aportes_no_iaavim = [
        AporteItem.model_validate(a) for a in tramite.aportes_rel
    ]
    return tramite


def attach_comite_output_fields(comite: ComiteFomento) -> ComiteFomento:
    """Adjunta `integrantes` como atributo plano para ComiteFomentoOut."""
    comite.integrantes = [IntegranteItem.model_validate(i) for i in comite.integrantes_rel]
    return comite
