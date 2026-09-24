# tests/test_alta_equipo.py
"""Alta de cuentas del equipo con link de activacion (72 h, un solo uso).

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""
import uuid

import pytest


def _rol_id(db_session, nombre):
    from src.models.user_models import Role

    db_session.rollback()
    return db_session.query(Role).filter(Role.rol == nombre).first().id


def _token(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


@pytest.fixture
def alta(client, admin_headers, db_session):
    def _alta(roles=("gestor_juridico",), email=None, headers=None):
        return client.post("/admin_user/users", headers=headers or admin_headers, json={
            "email": email or f"nuevo-{uuid.uuid4().hex[:6]}@iaavim.gob.ar",
            "role_ids": [_rol_id(db_session, r) for r in roles],
        })
    return _alta


def test_alta_crea_cuenta_de_equipo_pendiente_con_link(alta):
    resp = alta()
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["tipo_cuenta"] == "equipo"
    assert body["user"]["pendiente_activacion"] is True
    assert "/activar-cuenta/" in body["activation_url"]
    assert body["email_enviado"] is False  # sin SMTP en los tests


def test_la_cuenta_pendiente_no_puede_entrar(alta, client):
    body = alta().json()
    login = client.post("/users/token", data={"username": body["user"]["email"], "password": "Test1234"})
    assert login.status_code in (400, 401)


def test_alta_con_rol_de_ciudadano_es_409(alta):
    assert alta(roles=("user",)).status_code == 409


def test_alta_con_email_existente_es_409_y_no_toca_la_cuenta(alta, create_user, db_session):
    """Review Focus 2."""
    from src.models.user_models import User

    email = f"ya-{uuid.uuid4().hex[:6]}@x.com"
    create_user(email, roles=["user"])
    assert alta(email=email).status_code == 409
    db_session.rollback()
    assert db_session.query(User).filter(User.email == email).first().tipo_cuenta == "ciudadano"


def test_activar_define_la_contrasena_y_permite_entrar(alta, client):
    body = alta().json()
    token = _token(body["activation_url"])
    resp = client.post(f"/users/activar/{token}", json={"password": "Nueva1234"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["pendiente_activacion"] is False
    login = client.post("/users/token", data={"username": body["user"]["email"], "password": "Nueva1234"})
    assert login.status_code == 200, login.text


def test_activar_valida_la_contrasena(alta, client):
    token = _token(alta().json()["activation_url"])
    assert client.post(f"/users/activar/{token}", json={"password": "corta"}).status_code in (400, 422)


def test_el_link_es_de_un_solo_uso(alta, client):
    """Review Focus 3."""
    token = _token(alta().json()["activation_url"])
    assert client.post(f"/users/activar/{token}", json={"password": "Nueva1234"}).status_code == 200
    segunda = client.post(f"/users/activar/{token}", json={"password": "Otra12345"})
    assert segunda.status_code == 400
    assert "ya se usó" in segunda.json()["detail"]


def test_un_token_de_recuperacion_no_activa(client, create_user):
    """Review Focus 3: tipo equivocado."""
    from src.token_utils import create_access_token

    user, _ = create_user(f"r-{uuid.uuid4().hex[:6]}@x.com", roles=["user"])
    recover = create_access_token(data={"sub": user.id}, expires_delta=60, type="recover")
    assert client.post(f"/users/activar/{recover}", json={"password": "Nueva1234"}).status_code == 401


def test_link_vencido(client, alta, db_session):
    from datetime import datetime, timedelta, timezone

    from src.models.user_models import TokenRecovery

    token = _token(alta().json()["activation_url"])
    db_session.rollback()
    db_session.query(TokenRecovery).filter(TokenRecovery.token_payload == token).update(
        {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}
    )
    db_session.commit()
    resp = client.post(f"/users/activar/{token}", json={"password": "Nueva1234"})
    assert resp.status_code == 400 and "venció" in resp.json()["detail"]


def test_regenerar_link_invalida_el_anterior(alta, client, admin_headers):
    body = alta().json()
    viejo = _token(body["activation_url"])
    nuevo = client.post(f"/admin_user/users/{body['user']['id']}/activation-link", headers=admin_headers)
    assert nuevo.status_code == 200, nuevo.text
    assert client.post(f"/users/activar/{viejo}", json={"password": "Nueva1234"}).status_code == 400
    nuevo_token = _token(nuevo.json()["activation_url"])
    assert client.post(f"/users/activar/{nuevo_token}", json={"password": "Nueva1234"}).status_code == 200


def test_no_se_regenera_el_link_de_una_cuenta_activa(alta, client, admin_headers):
    body = alta().json()
    client.post(f"/users/activar/{_token(body['activation_url'])}", json={"password": "Nueva1234"})
    resp = client.post(f"/admin_user/users/{body['user']['id']}/activation-link", headers=admin_headers)
    assert resp.status_code == 409


def test_sin_roles_manage_no_se_da_de_alta(alta, create_user):
    _, headers = create_user(f"g-{uuid.uuid4().hex[:6]}@x.com", roles=["gestor_fomento"])
    assert alta(headers=headers).status_code == 403


def test_solo_un_admin_da_de_alta_admins(alta, create_user, db_session):
    from src.models.user_models import Permission, Role

    db_session.rollback()
    perm = db_session.query(Permission).filter(Permission.code == "roles:manage").first()
    rol = Role(rol=f"rrhh_{uuid.uuid4().hex[:6]}", is_system=False)
    rol.permissions = [perm]
    db_session.add(rol)
    db_session.commit()
    _, headers = create_user(f"rrhh-{uuid.uuid4().hex[:6]}@x.com", roles=[rol.rol])
    assert alta(roles=("admin",), headers=headers).status_code == 403
    assert alta(roles=("lectura",), headers=headers).status_code == 201


# --- Revision final ---------------------------------------------------------
def test_un_link_viejo_no_sirve_si_la_cuenta_ya_se_activo(alta, client, admin_headers):
    """Si la cuenta ya tiene contrasena (recuperacion o cambio del admin), el
    link de alta que quedo dando vueltas no puede pisarla."""
    body = alta().json()
    token = _token(body["activation_url"])
    resp = client.put(f"/admin_user/users/{body['user']['id']}", headers=admin_headers,
                      json={"password": "Propia1234"})
    assert resp.status_code == 200, resp.text
    viejo = client.post(f"/users/activar/{token}", json={"password": "Ajena12345"})
    assert viejo.status_code == 400
    assert "ya está activa" in viejo.json()["detail"]
    login = client.post("/users/token", data={"username": body["user"]["email"], "password": "Propia1234"})
    assert login.status_code == 200


def test_una_contrasena_demasiado_larga_es_422_y_no_500(alta, client):
    token = _token(alta().json()["activation_url"])
    resp = client.post(f"/users/activar/{token}", json={"password": "Aa1" + "x" * 80})
    assert resp.status_code == 422, resp.text


def test_un_jwt_vencido_dice_que_el_link_vencio(client, create_user):
    """El JWT y el registro vencen juntos: el mensaje tiene que ser el claro, y
    no un 401 (que el frontend tomaria como sesion vencida)."""
    from src.token_utils import create_access_token

    user, _ = create_user(f"v-{uuid.uuid4().hex[:6]}@x.com", roles=["lectura"])
    vencido = create_access_token(data={"sub": user.id}, expires_delta=-1, type="activacion")
    resp = client.post(f"/users/activar/{vencido}", json={"password": "Nueva1234"})
    assert resp.status_code == 400, resp.text
    assert "venció" in resp.json()["detail"]


def test_dos_activaciones_simultaneas_solo_una_gana(alta, client, monkeypatch, SessionLocal):
    """Dos pedidos con el mismo link: el que llega segundo encontró el link
    vigente al leerlo, pero el primero lo consumió antes de que éste guarde.
    Se simula "el otro pedido ya confirmó" marcando el link como usado desde
    otra sesión en el medio del pedido (durante la validación de la clave)."""
    from src.models.user_models import TokenRecovery
    from src.routes import user_routes

    body = alta().json()
    token = _token(body["activation_url"])
    validar_original = user_routes.validar_password

    def el_otro_pedido_gano(password):
        validar_original(password)
        otra = SessionLocal()
        otra.query(TokenRecovery).filter(TokenRecovery.token_payload == token).update(
            {"is_active": False}
        )
        otra.commit()
        otra.close()

    monkeypatch.setattr(user_routes, "validar_password", el_otro_pedido_gano)
    resp = client.post(f"/users/activar/{token}", json={"password": "Perdedora1"})
    assert resp.status_code == 400, resp.text
    assert "ya se usó" in resp.json()["detail"]
    login = client.post("/users/token", data={"username": body["user"]["email"], "password": "Perdedora1"})
    assert login.status_code in (400, 401)


def test_una_clave_invalida_no_consume_el_link(alta, client):
    token = _token(alta().json()["activation_url"])
    assert client.post(f"/users/activar/{token}", json={"password": "corta"}).status_code in (400, 422)
    assert client.post(f"/users/activar/{token}", json={"password": "Nueva1234"}).status_code == 200


@pytest.mark.parametrize("regenerar", [False, True])
def test_el_mail_de_activacion_sale_despues_del_commit(
    alta, client, admin_headers, monkeypatch, SessionLocal, regenerar
):
    """Si el mail salía antes del commit y el commit fallaba, la persona
    recibía un link que no existía en la base."""
    from src.models.user_models import TokenRecovery
    from src.routes import admin_routes

    vistos = []

    def enviar(email, url):
        otra = SessionLocal()
        vistos.append(
            otra.query(TokenRecovery).filter(TokenRecovery.token_payload == _token(url)).first()
            is not None
        )
        otra.close()

    monkeypatch.setattr(admin_routes, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(admin_routes, "send_activation_email", enviar)
    body = alta().json()
    if regenerar:
        body = client.post(
            f"/admin_user/users/{body['user']['id']}/activation-link", headers=admin_headers
        ).json()
    assert body["email_enviado"] is True
    assert vistos and vistos[-1] is True


def test_si_el_mail_falla_el_link_igual_se_devuelve(alta, monkeypatch):
    from src.routes import admin_routes

    def falla(email, url):
        raise ConnectionError("SMTP caído")

    monkeypatch.setattr(admin_routes, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(admin_routes, "send_activation_email", falla)
    resp = alta()
    assert resp.status_code == 201, resp.text
    assert resp.json()["email_enviado"] is False
    assert "/activar-cuenta/" in resp.json()["activation_url"]


def test_listado_filtra_pendientes_de_activacion(alta, client, admin_headers):
    pendiente = alta().json()["user"]["email"]
    activa = alta().json()
    client.post(f"/users/activar/{_token(activa['activation_url'])}", json={"password": "Nueva1234"})

    def emails(valor):
        resp = client.get(
            f"/admin_user/users?tipo_cuenta=equipo&pendiente_activacion={valor}&limit=200",
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        return {u["email"] for u in resp.json()["items"]}

    assert pendiente in emails("true") and activa["user"]["email"] not in emails("true")
    assert activa["user"]["email"] in emails("false") and pendiente not in emails("false")
