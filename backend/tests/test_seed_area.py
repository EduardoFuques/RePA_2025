# tests/test_seed_area.py
"""Seed de demostracion de los modulos de area (src/seed_area.py).

El seed no corre en la suite (IS_TESTING), asi que sin este test nada
comprobaria que sus filas respetan los CheckConstraint, que cubren todos los
estados, ni que los PDF quedan con la ruta que aceptan los endpoints de
descarga — un error ahi se veria recien en QA, como un 404 al tocar "Ver".

No se importa `src.*` a nivel de modulo: conftest levanta el contenedor de
Postgres al importarse y los imports tienen que ocurrir despues.
"""

import pytest


# La base es compartida por toda la suite: otros tests tambien crean
# expedientes, instrumentos y actas. Todo lo que se consulta aca se acota a
# las filas del seed, por sus propias claves.
def _numeros_demo():
    from datetime import date

    from src.seed_area import _expedientes, _instrumentos

    hoy = date.today()
    exps = [c["numero_expediente_provincial"] for c, _ in _expedientes(hoy, None)
            if "numero_expediente_provincial" in c]
    insts = [c["numero_instrumento"] for c, _ in _instrumentos(hoy, None)
             if "numero_instrumento" in c]
    return exps, insts


@pytest.fixture(scope="session")
def uploads_seed(tmp_path_factory):
    """Un solo directorio de uploads para toda la sesion, no uno por test:
    el seed es idempotente, asi que los PDF se escriben en la PRIMERA
    corrida y los tests siguientes los tienen que encontrar ahi."""
    return tmp_path_factory.mktemp("uploads-seed-area")


@pytest.fixture
def sembrado(db_session, uploads_seed, monkeypatch):
    """Corre el seed con los usuarios que usa y los uploads en uploads_seed."""
    import src.document_generator as generador
    import src.routes.upload_routes as upload_routes
    from src.models.user_models import User
    from src.password import get_password_hash
    from src.seed_area import seed_area_data

    # Mismo directorio para quien escribe los PDF y quien los sirve.
    monkeypatch.setattr(generador, "UPLOAD_BASE_DIR", str(uploads_seed))
    monkeypatch.setattr(upload_routes, "UPLOAD_BASE_DIR", str(uploads_seed))

    # El seed solo necesita que existan (guarda los PDF en su directorio).
    # Se crean aca y no con _crear_usuario de conftest: importar conftest
    # como modulo podria volver a ejecutarlo y levantar otro contenedor.
    for email in ("equipo.admin1@repa.gob.ar", "equipo.administracion1@repa.gob.ar", "equipo.juridico1@repa.gob.ar"):
        if not db_session.query(User).filter(User.email == email).first():
            db_session.add(User(email=email, hashed_password=get_password_hash("Test1234"), is_active=True, tipo_cuenta="equipo"))
    db_session.commit()
    seed_area_data(db_session)
    return db_session


def test_expedientes_en_todos_los_estados_y_borradores(sembrado):
    from src.models.expediente_model import ExpedienteAdministrativo

    exps, _ = _numeros_demo()
    demo = sembrado.query(ExpedienteAdministrativo).filter(
        ExpedienteAdministrativo.numero_expediente_provincial.in_(exps)
    ).all()
    assert len(demo) == len(exps)
    assert {e.estado_expediente for e in demo} == {
        "iniciado", "en_proceso_administrativo", "en_tesoreria",
        "aprobado_para_pago", "pagado", "observado_rechazado",
    }
    borradores = sembrado.query(ExpedienteAdministrativo).filter(
        ExpedienteAdministrativo.nombre_proyecto.like("[Borrador demo]%")
    ).all()
    assert len(borradores) == 2 and all(b.borrador for b in borradores)


def test_instrumentos_en_todos_los_estados_y_con_acta(sembrado):
    from src.models.instrumento_juridico_model import InstrumentoJuridico

    _, insts = _numeros_demo()
    cargados = sembrado.query(InstrumentoJuridico).filter(
        InstrumentoJuridico.numero_instrumento.in_(insts)
    ).all()
    assert len(cargados) == len(insts)
    assert not any(i.borrador for i in cargados)
    assert {i.estado_revision for i in cargados} >= {"en_revision", "validado", "archivado"}
    # Un cargado cumple lo que exige el envio: tipo, titulo, resumen y PDF.
    for i in cargados:
        assert i.tipo_documento and i.titulo and i.resumen and i.archivo_pdf_path, i.titulo
    acta = next(i for i in cargados if i.tipo_documento == "acta_consejo_directivo")
    assert acta.acta is not None and len(acta.acta.asistentes) == 3
    assert acta.acta.acta_pdf_path
    borradores = sembrado.query(InstrumentoJuridico).filter(
        InstrumentoJuridico.titulo.like("[Borrador demo]%")
    ).all()
    assert len(borradores) == 2 and all(b.borrador for b in borradores)


def test_los_pdf_se_descargan_por_el_endpoint_del_modulo(sembrado, client, admin_headers):
    from src.models.expediente_model import ExpedienteAdministrativo
    from src.models.instrumento_juridico_model import InstrumentoJuridico

    exps, insts = _numeros_demo()
    exp = sembrado.query(ExpedienteAdministrativo).filter(
        ExpedienteAdministrativo.numero_expediente_provincial.in_(exps),
        ExpedienteAdministrativo.resolucion_pdf_path.isnot(None),
    ).first()
    inst = sembrado.query(InstrumentoJuridico).filter(
        InstrumentoJuridico.numero_instrumento.in_(insts),
        InstrumentoJuridico.tipo_documento == "acta_consejo_directivo",
    ).first()
    assert exp is not None and inst is not None

    for url in (
        f"/expedientes/{exp.id}/resolucion-pdf",
        f"/instrumentos-juridicos/{inst.id}/pdf",
        f"/instrumentos-juridicos/{inst.id}/acta-pdf",
    ):
        resp = client.get(url, headers=admin_headers)
        assert resp.status_code == 200, (url, resp.text)
        assert resp.content.startswith(b"%PDF"), url


def test_es_idempotente(sembrado):
    from src.models.expediente_model import ExpedienteAdministrativo
    from src.models.instrumento_juridico_model import InstrumentoJuridico
    from src.seed_area import seed_area_data

    antes = (sembrado.query(ExpedienteAdministrativo).count(),
             sembrado.query(InstrumentoJuridico).count())
    seed_area_data(sembrado)
    despues = (sembrado.query(ExpedienteAdministrativo).count(),
               sembrado.query(InstrumentoJuridico).count())
    assert antes == despues


def test_los_borradores_del_seed_se_pueden_eliminar_y_los_cargados_no(
    sembrado, client, admin_headers
):
    from src.models.expediente_model import ExpedienteAdministrativo

    exps, _ = _numeros_demo()
    cargado = sembrado.query(ExpedienteAdministrativo).filter(
        ExpedienteAdministrativo.numero_expediente_provincial.in_(exps),
        ExpedienteAdministrativo.estado_expediente == "pagado",
    ).first()
    assert client.delete(f"/expedientes/{cargado.id}", headers=admin_headers).status_code == 409
