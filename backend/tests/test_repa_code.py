# tests/test_repa_code.py
"""Tests de la Fase 1 del Código RePA: generación secuencial y ciclo de vida."""
import pytest

from src.models.registro_lifecycle import EstadoRegistro, RepaCodeCounter
from src.services.repa_code_service import (
    ANCHO_SECUENCIA,
    PREFIJOS,
    TipoEntidadInvalido,
    build_codigo,
    generar_codigo_repa,
)


def test_build_codigo_formato():
    assert build_codigo("PF", 1) == "PF" + "1".zfill(ANCHO_SECUENCIA)
    assert build_codigo("PJ", 42) == "PJ000042"
    assert build_codigo("ESA", 7) == "ESA000007"


def test_build_codigo_tipo_invalido():
    with pytest.raises(TipoEntidadInvalido):
        build_codigo("XX", 1)


def test_as_agam_no_tienen_prefijo_propio():
    """AS y AGAM no emiten código RePA propio — usan el de la Persona
    Física titular como código de trámite (ver lifecycle_service)."""
    with pytest.raises(TipoEntidadInvalido):
        build_codigo("AS", 1)
    with pytest.raises(TipoEntidadInvalido):
        build_codigo("AGAM", 1)


def test_generar_codigo_secuencial_por_tipo(db_session):
    """Cada tipo lleva su propia secuencia, independiente de los demás."""
    primero = generar_codigo_repa(db_session, "PF")
    segundo = generar_codigo_repa(db_session, "PF")
    otro_tipo = generar_codigo_repa(db_session, "PJ")
    db_session.commit()

    assert primero != segundo
    # El segundo PF es exactamente uno más que el primero.
    n1 = int(primero[len("PF"):])
    n2 = int(segundo[len("PF"):])
    assert n2 == n1 + 1
    # PJ arranca su propia secuencia.
    assert otro_tipo.startswith("PJ")


def test_generar_codigo_crea_contador(db_session):
    generar_codigo_repa(db_session, "PJ")
    db_session.commit()
    counter = (
        db_session.query(RepaCodeCounter)
        .filter(RepaCodeCounter.tipo == "PJ")
        .first()
    )
    assert counter is not None
    assert counter.last_value >= 1


def test_generar_codigo_unico_en_lote(db_session):
    """Una tanda de emisiones no produce duplicados."""
    codigos = {generar_codigo_repa(db_session, "ESA") for _ in range(25)}
    db_session.commit()
    assert len(codigos) == 25


def test_todos_los_tipos_tienen_prefijo():
    """Solo PF/PJ/ESA emiten código RePA propio; AS/AGAM heredan el de la PF titular."""
    assert set(PREFIJOS) == {"PF", "PJ", "ESA"}


def test_estado_inicial_borrador(db_session):
    """Una entidad registrable recién creada arranca en estado 'borrador'."""
    from src.models.user_models import User
    from src.models.persona_fisica_model import PersonaFisica

    user = User(email="lifecycle_pf@example.com", hashed_password="x")
    db_session.add(user)
    db_session.flush()

    pf = PersonaFisica(user_id=user.id, acepta_terminos=False)
    db_session.add(pf)
    db_session.flush()

    assert pf.estado == EstadoRegistro.borrador.value
    assert pf.codigo_repa is None
    db_session.rollback()
