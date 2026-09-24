# tests/test_tipo_cuenta.py
"""Tipo de cuenta (ciudadano / equipo). Ver
docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md.

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""
import importlib.util
import pathlib
import uuid


def _migracion():
    ruta = pathlib.Path(__file__).parents[1] / "alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py"
    spec = importlib.util.spec_from_file_location("migracion_tipo_cuenta", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_es_rol_de_equipo():
    from src.rbac import es_rol_de_equipo

    assert not es_rol_de_equipo("user")
    assert not es_rol_de_equipo("estudiante")
    assert es_rol_de_equipo("gestor_fomento")
    assert es_rol_de_equipo("un_rol_personalizado")


def test_la_migracion_convierte_las_cuentas_mixtas(db_session):
    from src.models.user_models import Role, User

    def rol(nombre):
        r = db_session.query(Role).filter(Role.rol == nombre).first()
        if not r:
            r = Role(rol=nombre)
            db_session.add(r)
            db_session.flush()
        return r

    mixta = User(email=f"mixta-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    mixta.roles = [rol("user"), rol("gestor_fomento")]
    ciudadana = User(email=f"ciu-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    ciudadana.roles = [rol("user")]
    db_session.add_all([mixta, ciudadana])
    db_session.commit()

    convertidas = _migracion()._convertir_cuentas_de_equipo(db_session.connection())
    db_session.commit()
    db_session.expire_all()

    assert mixta.id in convertidas and ciudadana.id not in convertidas
    assert mixta.tipo_cuenta == "equipo"
    assert {r.rol for r in mixta.roles} == {"gestor_fomento"}
    assert ciudadana.tipo_cuenta == "ciudadano"
    assert {r.rol for r in ciudadana.roles} == {"user"}


# --- require_ciudadano -----------------------------------------------------
import pytest  # noqa: E402

RUTAS_CIUDADANO = [
    ("get", "/persona-fisica/me"),
    ("get", "/persona-juridica/me"),
    ("get", "/asociacion/me"),
    ("get", "/esa/me"),
    ("get", "/obras/me"),
    ("get", "/exhibiciones/salas/me"),
    ("get", "/rodajes/me"),
    ("get", "/fomento/tramites/me"),
    ("get", "/fomento/evaluadores/me"),
    ("post", "/users/me/become-estudiante"),
    ("get", "/upload/my-dni"),
]


def _como_equipo(db_session, user):
    from src.models.user_models import User

    db_session.query(User).filter(User.id == user.id).update({"tipo_cuenta": "equipo"})
    db_session.commit()


@pytest.fixture
def equipo_headers(create_user, db_session):
    user, headers = create_user(f"equipo-{uuid.uuid4().hex[:6]}@x.com", roles=["gestor_fomento"])
    _como_equipo(db_session, user)
    return headers


@pytest.fixture
def ciudadano_headers(create_user):
    # Cuenta propia por test: become-estudiante le cambia los roles.
    _, headers = create_user(f"ciu-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    return headers


@pytest.mark.parametrize("metodo,ruta", RUTAS_CIUDADANO)
def test_el_equipo_no_usa_endpoints_de_ciudadano(client, equipo_headers, metodo, ruta):
    resp = getattr(client, metodo)(ruta, headers=equipo_headers)
    assert resp.status_code == 403, (ruta, resp.text)
    assert "cuentas del equipo" in resp.json()["detail"]


@pytest.mark.parametrize("metodo,ruta", RUTAS_CIUDADANO)
def test_el_ciudadano_si(client, ciudadano_headers, metodo, ruta):
    resp = getattr(client, metodo)(ruta, headers=ciudadano_headers)
    assert resp.status_code != 403, (ruta, resp.text)


def test_token_emitido_antes_de_la_conversion(client, create_user, db_session):
    """Review Focus 1: la dependencia lee la base, no el token."""
    user, headers = create_user(f"conv-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    assert client.get("/persona-fisica/me", headers=headers).status_code != 403
    _como_equipo(db_session, user)
    assert client.get("/persona-fisica/me", headers=headers).status_code == 403


def test_el_equipo_sube_adjuntos_de_area_pero_no_de_ciudadano(
    client, equipo_headers, tmp_path, monkeypatch
):
    import src.routes.upload_routes as upload_routes

    monkeypatch.setattr(upload_routes, "UPLOAD_BASE_DIR", str(tmp_path))
    pdf = {"file": ("a.pdf", b"%PDF-1.4 x", "application/pdf")}
    area = client.post("/upload/document/instrumento_juridico", headers=equipo_headers, files=pdf)
    assert area.status_code == 200, area.text
    ciudadano = client.post("/upload/document/estatuto", headers=equipo_headers, files=pdf)
    assert ciudadano.status_code == 403


# --- Reglas de roles, /users/me y listado -----------------------------------
def _rol_id(db_session, nombre):
    from src.models.user_models import Role

    rol = db_session.query(Role).filter(Role.rol == nombre).first()
    if not rol:
        rol = Role(rol=nombre)
        db_session.add(rol)
        db_session.commit()
    return rol.id


def test_a_un_ciudadano_no_se_le_da_un_rol_de_equipo(client, admin_headers, create_user, db_session):
    user, _ = create_user(f"c-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    resp = client.put(f"/admin_user/users/{user.id}/roles", headers=admin_headers,
                      json={"add": [_rol_id(db_session, "gestor_fomento")], "remove": []})
    assert resp.status_code == 409, resp.text


def test_a_una_cuenta_de_equipo_no_se_le_da_user_ni_se_la_deja_sin_roles(
    client, admin_headers, create_user, db_session
):
    user, _ = create_user(f"e-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    _como_equipo(db_session, user)
    url = f"/admin_user/users/{user.id}/roles"
    con_user = client.put(url, headers=admin_headers, json={"add": [_rol_id(db_session, "user")], "remove": []})
    assert con_user.status_code == 409, con_user.text
    sin_roles = client.put(url, headers=admin_headers, json={"add": [], "remove": [_rol_id(db_session, "lectura")]})
    assert sin_roles.status_code == 409, sin_roles.text


def test_admin_no_requiere_persona_fisica(client, admin_headers, create_user, db_session):
    user, _ = create_user(f"a-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    _como_equipo(db_session, user)
    resp = client.put(f"/admin_user/users/{user.id}/roles", headers=admin_headers,
                      json={"add": [_rol_id(db_session, "admin")], "remove": []})
    assert resp.status_code == 200, resp.text


def test_me_expone_tipo_de_cuenta(client, ciudadano_headers):
    body = client.get("/users/me", headers=ciudadano_headers).json()
    assert body["tipo_cuenta"] == "ciudadano" and body["pendiente_activacion"] is False


def test_listado_filtra_por_tipo(client, admin_headers, create_user, db_session):
    user, _ = create_user(f"l-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    _como_equipo(db_session, user)
    body = client.get("/admin_user/users?tipo_cuenta=equipo&limit=200", headers=admin_headers).json()
    assert body["items"] and all(u["tipo_cuenta"] == "equipo" for u in body["items"])
    assert user.id in {u["id"] for u in body["items"]}


def test_el_registro_crea_cuentas_de_ciudadano(client, db_session):
    from src.models.user_models import User

    email = f"reg-{uuid.uuid4().hex[:6]}@x.com"
    client.post("/users/register", json={"email": email, "password": "Passw0rd1"})
    user = db_session.query(User).filter(User.email == email).first()
    assert user.tipo_cuenta == "ciudadano" and user.password_definida_at is not None


def test_la_migracion_no_deja_pendientes_a_las_cuentas_sin_created_at(db_session, create_user):
    """Una cuenta vieja sin created_at quedaba con password_definida_at NULL:
    "pendiente de activacion", sin poder entrar."""
    from src.models.user_models import User

    user, _ = create_user(f"vieja-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    db_session.rollback()
    db_session.query(User).filter(User.id == user.id).update(
        {"created_at": None, "password_definida_at": None}
    )
    _migracion()._marcar_contrasenas_existentes(db_session.connection())
    vieja = db_session.query(User).filter(User.id == user.id).first()
    db_session.refresh(vieja)
    assert vieja.password_definida_at is not None
    db_session.rollback()
