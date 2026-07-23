# tests/test_lifecycle.py
"""Tests de la Fase 2: máquina de estados del ciclo de vida y gating del Padrón RePA."""
import uuid

import pytest
from fastapi import HTTPException

from src.models.asociacion_model import Asociacion
from src.models.obra_audiovisual_model import ObraAudiovisual
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica
from src.models.registro_lifecycle import EstadoRegistro
from src.models.user_models import User
from src.services import lifecycle_service as ls


def _nuevo_user(db):
    user = User(email=f"lc_{uuid.uuid4().hex[:8]}@example.com", hashed_password="x")
    db.add(user)
    db.flush()
    return user


def _nueva_pj(db):
    user = _nuevo_user(db)
    pj = PersonaJuridica(user_id=user.id)
    db.add(pj)
    db.flush()
    return pj


def _nueva_pf(db, codigo_repa=None, estado=None):
    user = _nuevo_user(db)
    pf = PersonaFisica(user_id=user.id)
    if codigo_repa:
        pf.codigo_repa = codigo_repa
    if estado:
        pf.estado = estado
    db.add(pf)
    db.flush()
    return pf


# --------------------------------------------------------------------------- #
# Máquina de estados                                                          #
# --------------------------------------------------------------------------- #


def test_flujo_completo_hasta_aprobado_emite_codigo(db_session):
    pj = _nueva_pj(db_session)
    revisor = _nuevo_user(db_session)
    assert pj.estado == EstadoRegistro.borrador.value

    ls.enviar_a_revision(db_session, pj)
    assert pj.estado == EstadoRegistro.enviado.value
    assert pj.fecha_envio is not None

    ls.tomar_para_revision(db_session, pj)
    assert pj.estado == EstadoRegistro.en_revision.value
    assert pj.fecha_revision is not None

    codigo = ls.aprobar(db_session, pj, revisor_id=revisor.id)
    assert pj.estado == EstadoRegistro.aprobado.value
    assert codigo.startswith("PJ")
    assert pj.codigo_repa == codigo
    assert pj.revisado_por == revisor.id
    assert pj.fecha_vigencia_desde is not None
    assert pj.fecha_vigencia_hasta is not None
    assert pj.fecha_vigencia_hasta > pj.fecha_vigencia_desde


def test_transicion_invalida_lanza_error(db_session):
    pj = _nueva_pj(db_session)
    # No se puede aprobar directamente desde borrador.
    with pytest.raises(ls.TransicionInvalida):
        ls.aprobar(db_session, pj)


def test_observar_devuelve_a_usuario_y_permite_reenviar(db_session):
    pj = _nueva_pj(db_session)
    ls.enviar_a_revision(db_session, pj)
    ls.tomar_para_revision(db_session, pj)

    ls.observar(db_session, pj, motivo="Falta el estatuto")
    assert pj.estado == EstadoRegistro.observado.value
    assert pj.motivo_observacion == "Falta el estatuto"

    # Tras corregir, el usuario reenvía.
    ls.enviar_a_revision(db_session, pj)
    assert pj.estado == EstadoRegistro.enviado.value


def test_rechazar_es_terminal(db_session):
    pj = _nueva_pj(db_session)
    ls.enviar_a_revision(db_session, pj)
    ls.tomar_para_revision(db_session, pj)
    ls.rechazar(db_session, pj, motivo="No cumple requisitos")
    assert pj.estado == EstadoRegistro.rechazado.value
    assert pj.motivo_rechazo == "No cumple requisitos"
    # Desde rechazado no hay transiciones permitidas.
    with pytest.raises(ls.TransicionInvalida):
        ls.enviar_a_revision(db_session, pj)


def test_codigo_inmutable_si_ya_existe(db_session):
    pj = _nueva_pj(db_session)
    pj.codigo_repa = "PJ999999"
    ls.enviar_a_revision(db_session, pj)
    ls.tomar_para_revision(db_session, pj)
    codigo = ls.aprobar(db_session, pj)
    assert codigo == "PJ999999"  # no se regenera


def test_vencer_y_renovar(db_session):
    pj = _nueva_pj(db_session)
    ls.enviar_a_revision(db_session, pj)
    ls.tomar_para_revision(db_session, pj)
    ls.aprobar(db_session, pj)
    ls.marcar_vencido(db_session, pj)
    assert pj.estado == EstadoRegistro.vencido.value
    ls.renovar(db_session, pj)
    assert pj.estado == EstadoRegistro.vigente.value


# --------------------------------------------------------------------------- #
# Emisión de código RePA en el envío (decisión de negocio 2026-07-19)         #
# --------------------------------------------------------------------------- #


def test_emitir_codigo_repa_propio_en_pf(db_session):
    """PF emite su propio código; llamar dos veces no lo regenera (inmutable)."""
    pf = _nueva_pf(db_session)
    codigo = ls.emitir_codigo_repa_propio(db_session, pf)
    assert codigo.startswith("PF")
    assert pf.codigo_repa == codigo

    # Segunda llamada: no regenera.
    codigo2 = ls.emitir_codigo_repa_propio(db_session, pf)
    assert codigo2 == codigo


def test_heredar_codigo_repa_titular_as(db_session):
    """AS no genera código propio: hereda el de la PF titular como código de trámite."""
    pf = _nueva_pf(db_session, codigo_repa="PF000123")
    asoc = Asociacion(user_id=pf.user_id)
    db_session.add(asoc)
    db_session.flush()

    resultado = ls.heredar_codigo_repa_titular(db_session, asoc, pf)

    assert resultado == "PF000123"
    assert asoc.codigo_repa_titular == "PF000123"
    assert asoc.codigo_repa is None  # AS nunca tiene identidad propia


def test_heredar_codigo_repa_titular_sin_pf_no_rompe(db_session):
    """Si la PF titular todavía no tiene código (no debería pasar en el flujo
    normal), no falla — deja el campo sin setear para reintentar después."""
    pf = _nueva_pf(db_session)  # sin codigo_repa
    asoc = Asociacion(user_id=pf.user_id)
    db_session.add(asoc)
    db_session.flush()

    resultado = ls.heredar_codigo_repa_titular(db_session, asoc, pf)

    assert resultado is None
    assert asoc.codigo_repa_titular is None


def test_procesar_envio_pf_emite_codigo_propio(db_session):
    pf = _nueva_pf(db_session)
    assert pf.estado == EstadoRegistro.borrador.value

    ls.procesar_envio_si_corresponde(db_session, pf, {"borrador": False})

    assert pf.estado == EstadoRegistro.enviado.value
    assert pf.fecha_envio is not None
    assert pf.codigo_repa is not None
    assert pf.codigo_repa.startswith("PF")


def test_procesar_envio_agam_hereda_codigo_titular(db_session):
    pf = _nueva_pf(db_session, codigo_repa="PF000042")
    obra = ObraAudiovisual(user_id=pf.user_id, titulo="Corto de prueba")
    db_session.add(obra)
    db_session.flush()
    assert obra.estado == EstadoRegistro.borrador.value

    ls.procesar_envio_si_corresponde(
        db_session, obra, {"borrador": False}, get_persona_fisica_titular=lambda: pf
    )

    assert obra.estado == EstadoRegistro.enviado.value
    assert obra.codigo_repa_titular == "PF000042"
    assert obra.codigo_repa is None  # AGAM nunca tiene identidad propia


def test_procesar_envio_es_idempotente(db_session):
    """Un segundo PUT con borrador:false (edición posterior al envío) no
    reenvía ni regenera nada — el estado ya no es 'borrador'."""
    pf = _nueva_pf(db_session)
    ls.procesar_envio_si_corresponde(db_session, pf, {"borrador": False})
    codigo_original = pf.codigo_repa
    fecha_envio_original = pf.fecha_envio

    # Segunda edición, también con borrador:false (el frontend lo manda siempre).
    ls.procesar_envio_si_corresponde(db_session, pf, {"borrador": False, "nombre": "X"})

    assert pf.codigo_repa == codigo_original
    assert pf.fecha_envio == fecha_envio_original


def test_procesar_envio_no_dispara_en_guardado_de_borrador(db_session):
    """Guardar un borrador intermedio (borrador:true, o borrador ausente del
    payload) no debe emitir código ni cambiar el estado."""
    pf = _nueva_pf(db_session)
    ls.procesar_envio_si_corresponde(db_session, pf, {"borrador": True, "nombre": "X"})
    assert pf.estado == EstadoRegistro.borrador.value
    assert pf.codigo_repa is None

    ls.procesar_envio_si_corresponde(db_session, pf, {"nombre": "Y"})
    assert pf.estado == EstadoRegistro.borrador.value
    assert pf.codigo_repa is None


# --------------------------------------------------------------------------- #
# Gating: require_pf_aprobado                                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_gating_off_es_transparente(db_session, monkeypatch):
    import src.utils as utils

    monkeypatch.setattr(utils, "REPA_GATING_ENABLED", False)
    user = _nuevo_user(db_session)
    db_session.flush()
    current_user = {"id": user.id, "email": user.email, "roles": []}
    # Sin PF, pero con gating OFF debe pasar.
    result = await utils.require_pf_aprobado(current_user=current_user, db=db_session)
    assert result == current_user


@pytest.mark.asyncio
async def test_gating_on_sin_pf_aprobada_da_403(db_session, monkeypatch):
    import src.utils as utils

    monkeypatch.setattr(utils, "REPA_GATING_ENABLED", True)
    user = _nuevo_user(db_session)
    db_session.flush()
    current_user = {"id": user.id, "email": user.email, "roles": []}

    with pytest.raises(HTTPException) as exc:
        await utils.require_pf_aprobado(current_user=current_user, db=db_session)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_gating_on_con_pf_aprobada_pasa(db_session, monkeypatch):
    import src.utils as utils

    monkeypatch.setattr(utils, "REPA_GATING_ENABLED", True)
    user = _nuevo_user(db_session)
    pf = PersonaFisica(user_id=user.id, estado=EstadoRegistro.aprobado.value)
    db_session.add(pf)
    db_session.flush()
    current_user = {"id": user.id, "email": user.email, "roles": []}

    result = await utils.require_pf_aprobado(current_user=current_user, db=db_session)
    assert result == current_user


@pytest.mark.asyncio
async def test_gating_on_con_pf_solo_enviada_pasa(db_session, monkeypatch):
    """El código RePA se emite en el envío (no en la aprobación, que es
    post-lanzamiento) — el gate debe alcanzar con 'enviado', no exigir
    'aprobado' específicamente, o nadie podría registrar PJ/AS/AGAM hasta
    que exista el circuito de aprobación."""
    import src.utils as utils

    monkeypatch.setattr(utils, "REPA_GATING_ENABLED", True)
    user = _nuevo_user(db_session)
    # Código distintivo (no el formato real PFxxxxxx) para no colisionar con
    # códigos reales que la suite completa ya haya emitido en esta misma DB.
    pf = PersonaFisica(
        user_id=user.id, estado=EstadoRegistro.enviado.value, codigo_repa="PF-TEST-GATING"
    )
    db_session.add(pf)
    db_session.flush()
    current_user = {"id": user.id, "email": user.email, "roles": []}

    result = await utils.require_pf_aprobado(current_user=current_user, db=db_session)
    assert result == current_user


@pytest.mark.asyncio
async def test_gating_on_con_pf_en_borrador_da_403(db_session, monkeypatch):
    """PF existe pero todavía no se envió (sigue en borrador, sin código) —
    debe seguir bloqueado."""
    import src.utils as utils

    monkeypatch.setattr(utils, "REPA_GATING_ENABLED", True)
    user = _nuevo_user(db_session)
    pf = PersonaFisica(user_id=user.id)  # estado default: borrador
    db_session.add(pf)
    db_session.flush()
    current_user = {"id": user.id, "email": user.email, "roles": []}

    with pytest.raises(HTTPException) as exc:
        await utils.require_pf_aprobado(current_user=current_user, db=db_session)
    assert exc.value.status_code == 403
