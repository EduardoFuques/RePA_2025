"""
Tests del módulo de Fomento (el router más extenso del backend).

Matriz por endpoint: happy path + autenticación (401) + autorización admin (403)
+ validación (422) + ownership (404 entre usuarios) + 404 de recursos.

Fixtures compartidas (conftest.py): client, admin_headers, user_headers, create_user.
"""
import uuid

import pytest

# ---------------------------------------------------------------------------
# Fixtures de datos de Fomento
# ---------------------------------------------------------------------------


@pytest.fixture
def evento(client, admin_headers):
    """Crea un evento de fomento y devuelve su representación JSON."""
    resp = client.post(
        "/fomento/eventos",
        headers=admin_headers,
        json={"nombre": "Convocatoria Test", "anio_edicion": 2025, "tipo": "competitiva"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def linea(client, admin_headers, evento):
    """Crea una línea dentro del evento y devuelve su JSON."""
    resp = client.post(
        f"/fomento/eventos/{evento['id']}/lineas",
        headers=admin_headers,
        json={"nombre": "Línea Largometraje", "tope_por_proyecto": 1000000},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def tramite_owner(create_user):
    """Usuario regular fresco (un trámite por usuario → /me determinista)."""
    _user, headers = create_user(
        f"tramite_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
    )
    return headers


@pytest.fixture
def tramite(client, tramite_owner):
    """Crea un trámite para un usuario fresco y devuelve su JSON."""
    resp = client.post(
        "/fomento/tramites",
        headers=tramite_owner,
        json={"titulo_proyecto": "Mi Proyecto", "tipo_tramite": "ventanilla_continua"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def evaluador_owner(create_user):
    """Usuario regular fresco (un evaluador por usuario → /me determinista)."""
    _user, headers = create_user(
        f"evaluador_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
    )
    return headers


@pytest.fixture
def evaluador(client, evaluador_owner):
    """Crea un evaluador para un usuario fresco y devuelve su JSON."""
    resp = client.post(
        "/fomento/evaluadores",
        headers=evaluador_owner,
        json={"nombre_completo": "Eva Luadora", "email": "eva@example.com"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def second_user(create_user):
    """Segundo usuario regular distinto, para pruebas de aislamiento (ownership)."""
    _user, headers = create_user("otro_fomento@example.com", roles=["user"])
    return headers


# ---------------------------------------------------------------------------
# EVENTOS / CONVOCATORIAS (escritura solo admin, lectura autenticada)
# ---------------------------------------------------------------------------


class TestEventos:
    def test_create_requires_auth(self, client):
        resp = client.post("/fomento/eventos", json={})
        assert resp.status_code == 401

    def test_create_forbidden_for_regular_user(self, client, user_headers):
        resp = client.post(
            "/fomento/eventos",
            headers=user_headers,
            json={"nombre": "X", "anio_edicion": 2025, "tipo": "competitiva"},
        )
        assert resp.status_code == 403

    def test_create_validation_error(self, client, admin_headers):
        # Faltan campos requeridos (nombre, anio_edicion, tipo)
        resp = client.post("/fomento/eventos", headers=admin_headers, json={})
        assert resp.status_code == 422

    def test_create_and_get(self, client, admin_headers, evento):
        assert evento["nombre"] == "Convocatoria Test"
        assert evento["lineas"] == []
        resp = client.get(f"/fomento/eventos/{evento['id']}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == evento["id"]

    def test_get_not_found(self, client, admin_headers):
        resp = client.get("/fomento/eventos/99999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_list_returns_list(self, client, user_headers, evento):
        resp = client.get("/fomento/eventos", headers=user_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_activos(self, client, admin_headers, user_headers, evento):
        # El evento creado está en 'borrador'; al activarlo aparece en /activos
        upd = client.put(
            f"/fomento/eventos/{evento['id']}",
            headers=admin_headers,
            json={"estado": "activo"},
        )
        assert upd.status_code == 200
        resp = client.get("/fomento/eventos/activos", headers=user_headers)
        assert resp.status_code == 200
        assert any(e["id"] == evento["id"] for e in resp.json())

    def test_update_forbidden_for_regular_user(self, client, user_headers, evento):
        resp = client.put(
            f"/fomento/eventos/{evento['id']}",
            headers=user_headers,
            json={"nombre": "Hack"},
        )
        assert resp.status_code == 403

    def test_update_not_found(self, client, admin_headers):
        resp = client.put(
            "/fomento/eventos/99999999", headers=admin_headers, json={"nombre": "X"}
        )
        assert resp.status_code == 404

    def test_delete_and_then_404(self, client, admin_headers, evento):
        resp = client.delete(
            f"/fomento/eventos/{evento['id']}", headers=admin_headers
        )
        assert resp.status_code == 204
        resp2 = client.get(f"/fomento/eventos/{evento['id']}", headers=admin_headers)
        assert resp2.status_code == 404

    def test_delete_forbidden_for_regular_user(self, client, user_headers, evento):
        resp = client.delete(
            f"/fomento/eventos/{evento['id']}", headers=user_headers
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# LÍNEAS DE FOMENTO
# ---------------------------------------------------------------------------


class TestLineas:
    def test_create_under_evento(self, client, linea, evento):
        assert linea["evento_id"] == evento["id"]
        assert linea["vigente"] is True

    def test_create_forbidden_for_regular_user(self, client, user_headers, evento):
        resp = client.post(
            f"/fomento/eventos/{evento['id']}/lineas",
            headers=user_headers,
            json={"nombre": "X"},
        )
        assert resp.status_code == 403

    def test_create_evento_not_found(self, client, admin_headers):
        resp = client.post(
            "/fomento/eventos/99999999/lineas",
            headers=admin_headers,
            json={"nombre": "X"},
        )
        assert resp.status_code == 404

    def test_list_lineas(self, client, admin_headers, evento, linea):
        resp = client.get(
            f"/fomento/eventos/{evento['id']}/lineas", headers=admin_headers
        )
        assert resp.status_code == 200
        assert any(item["id"] == linea["id"] for item in resp.json())

    def test_update_linea(self, client, admin_headers, linea):
        resp = client.put(
            f"/fomento/lineas/{linea['id']}",
            headers=admin_headers,
            json={"vigente": False},
        )
        assert resp.status_code == 200
        assert resp.json()["vigente"] is False

    def test_update_linea_not_found(self, client, admin_headers):
        resp = client.put(
            "/fomento/lineas/99999999", headers=admin_headers, json={"vigente": False}
        )
        assert resp.status_code == 404

    def test_delete_linea(self, client, admin_headers, linea):
        resp = client.delete(
            f"/fomento/lineas/{linea['id']}", headers=admin_headers
        )
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# TRÁMITES (ownership por user_id)
# ---------------------------------------------------------------------------


class TestTramites:
    def test_create_requires_auth(self, client):
        resp = client.post("/fomento/tramites", json={})
        assert resp.status_code == 401

    def test_create_sets_owner(self, client, tramite):
        assert tramite["titulo_proyecto"] == "Mi Proyecto"
        assert tramite["user_id"]
        assert tramite["borrador"] is True

    def test_get_my_tramite(self, client, tramite_owner, tramite):
        resp = client.get("/fomento/tramites/me", headers=tramite_owner)
        assert resp.status_code == 200
        assert resp.json()["id"] == tramite["id"]

    def test_update_my_tramite(self, client, tramite_owner, tramite):
        resp = client.put(
            "/fomento/tramites/me",
            headers=tramite_owner,
            json={"titulo_proyecto": "Actualizado"},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo_proyecto"] == "Actualizado"

    def test_list_my_tramites(self, client, tramite_owner, tramite):
        resp = client.get("/fomento/tramites", headers=tramite_owner)
        assert resp.status_code == 200
        assert any(t["id"] == tramite["id"] for t in resp.json())

    def test_get_by_id_owner(self, client, tramite_owner, tramite):
        resp = client.get(f"/fomento/tramites/{tramite['id']}", headers=tramite_owner)
        assert resp.status_code == 200

    def test_get_by_id_other_user_is_404(self, client, second_user, tramite):
        # El segundo usuario no puede ver el trámite ajeno (filtrado por user_id)
        resp = client.get(f"/fomento/tramites/{tramite['id']}", headers=second_user)
        assert resp.status_code == 404

    def test_update_other_user_is_404(self, client, second_user, tramite):
        resp = client.put(
            f"/fomento/tramites/{tramite['id']}",
            headers=second_user,
            json={"titulo_proyecto": "Hack"},
        )
        assert resp.status_code == 404

    def test_delete_owner(self, client, tramite_owner, tramite):
        resp = client.delete(
            f"/fomento/tramites/{tramite['id']}", headers=tramite_owner
        )
        assert resp.status_code == 204

    def test_admin_list_all(self, client, admin_headers, tramite):
        resp = client.get("/fomento/tramites/admin", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_admin_list_forbidden_for_regular_user(self, client, user_headers):
        resp = client.get("/fomento/tramites/admin", headers=user_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# EVALUADORES (ownership por user_id)
# ---------------------------------------------------------------------------


class TestEvaluadores:
    def test_create_sets_owner(self, client, evaluador):
        assert evaluador["nombre_completo"] == "Eva Luadora"

    def test_get_my_evaluador(self, client, evaluador_owner, evaluador):
        resp = client.get("/fomento/evaluadores/me", headers=evaluador_owner)
        assert resp.status_code == 200
        assert resp.json()["id"] == evaluador["id"]

    def test_get_by_id_other_user_is_404(self, client, second_user, evaluador):
        resp = client.get(
            f"/fomento/evaluadores/{evaluador['id']}", headers=second_user
        )
        assert resp.status_code == 404

    def test_list_todos_requires_admin(self, client, user_headers):
        resp = client.get("/fomento/evaluadores/todos", headers=user_headers)
        assert resp.status_code == 403

    def test_list_todos_returns_non_draft(
        self, client, admin_headers, user_headers, evaluador, db_session
    ):
        # Regresión del bug `filter(not Evaluador.borrador)`: un evaluador con
        # borrador=False debe aparecer en /evaluadores/todos.
        from src.models.fomento_model import Evaluador

        ev = db_session.query(Evaluador).filter(Evaluador.id == evaluador["id"]).first()
        ev.borrador = False
        db_session.commit()

        resp = client.get("/fomento/evaluadores/todos", headers=admin_headers)
        assert resp.status_code == 200
        assert any(e["id"] == evaluador["id"] for e in resp.json())


# ---------------------------------------------------------------------------
# COMITÉS (solo admin)
# ---------------------------------------------------------------------------


class TestComites:
    def test_create_requires_admin(self, client, user_headers, evento):
        resp = client.post(
            "/fomento/comites",
            headers=user_headers,
            json={"evento_id": evento["id"], "tipo": "tecnico"},
        )
        assert resp.status_code == 403

    def test_create_evento_not_found(self, client, admin_headers):
        resp = client.post(
            "/fomento/comites",
            headers=admin_headers,
            json={"evento_id": 99999999, "tipo": "tecnico"},
        )
        assert resp.status_code == 404

    def test_create_get_and_delete(self, client, admin_headers, evento):
        create = client.post(
            "/fomento/comites",
            headers=admin_headers,
            json={"evento_id": evento["id"], "tipo": "tecnico", "nombre": "Comité A"},
        )
        assert create.status_code == 201, create.text
        comite = create.json()

        get = client.get(f"/fomento/comites/{comite['id']}", headers=admin_headers)
        assert get.status_code == 200

        listed = client.get(
            f"/fomento/comites?evento_id={evento['id']}", headers=admin_headers
        )
        assert listed.status_code == 200
        assert any(c["id"] == comite["id"] for c in listed.json())

        delete = client.delete(
            f"/fomento/comites/{comite['id']}", headers=admin_headers
        )
        assert delete.status_code == 204

    def test_list_requires_admin(self, client, user_headers):
        resp = client.get("/fomento/comites", headers=user_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DICTÁMENES (creación/listado solo admin)
# ---------------------------------------------------------------------------


class TestDictamenes:
    def test_create_requires_admin(self, client, user_headers):
        resp = client.post(
            "/fomento/dictamenes",
            headers=user_headers,
            json={"tramite_id": 1, "evaluador_id": 1, "tipo_dictamen": "tecnico"},
        )
        assert resp.status_code == 403

    def test_create_tramite_not_found(self, client, admin_headers, evaluador):
        resp = client.post(
            "/fomento/dictamenes",
            headers=admin_headers,
            json={
                "tramite_id": 99999999,
                "evaluador_id": evaluador["id"],
                "tipo_dictamen": "tecnico",
            },
        )
        assert resp.status_code == 404

    def test_create_evaluador_not_found(self, client, admin_headers, tramite):
        resp = client.post(
            "/fomento/dictamenes",
            headers=admin_headers,
            json={
                "tramite_id": tramite["id"],
                "evaluador_id": 99999999,
                "tipo_dictamen": "tecnico",
            },
        )
        assert resp.status_code == 404

    def test_create_and_list(self, client, admin_headers, tramite, evaluador):
        create = client.post(
            "/fomento/dictamenes",
            headers=admin_headers,
            json={
                "tramite_id": tramite["id"],
                "evaluador_id": evaluador["id"],
                "tipo_dictamen": "tecnico",
                "puntaje": 80,
            },
        )
        assert create.status_code == 201, create.text
        dictamen = create.json()

        listed = client.get(
            f"/fomento/dictamenes?tramite_id={tramite['id']}", headers=admin_headers
        )
        assert listed.status_code == 200
        assert any(d["id"] == dictamen["id"] for d in listed.json())

    def test_list_requires_admin(self, client, user_headers):
        resp = client.get("/fomento/dictamenes", headers=user_headers)
        assert resp.status_code == 403
