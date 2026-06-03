"""
Tests del módulo de Rodajes (Comisión de Filmaciones).

Matriz: happy path + 401 (sin auth) + 403 (admin-only) + 404 (recurso/ownership)
+ regla de negocio (solo se borran borradores).

Fixtures compartidas (conftest.py): client, admin_headers, user_headers, create_user.
"""
import uuid

import pytest


@pytest.fixture
def rodaje_owner(create_user):
    """Usuario regular fresco, dueño de los rodajes del test."""
    _user, headers = create_user(
        f"rodaje_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
    )
    return headers


def _crear_rodaje(client, headers, **extra):
    payload = {"titulo_produccion": "Mi Película", "anio_rodaje": 2025}
    payload.update(extra)
    resp = client.post("/rodajes/", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def rodaje(client, rodaje_owner):
    """Rodaje en estado borrador (eliminable) del usuario fresco."""
    return _crear_rodaje(client, rodaje_owner, borrador=True)


# ---------------------------------------------------------------------------
# CRUD del usuario (ownership por user_id)
# ---------------------------------------------------------------------------


class TestRodajeUsuario:
    def test_create_requires_auth(self, client):
        resp = client.post("/rodajes/", json={})
        assert resp.status_code == 401

    def test_create_sets_owner(self, client, rodaje):
        assert rodaje["titulo_produccion"] == "Mi Película"
        assert rodaje["user_id"]

    def test_list_my_rodajes(self, client, rodaje_owner, rodaje):
        resp = client.get("/rodajes/me", headers=rodaje_owner)
        assert resp.status_code == 200
        assert any(r["id"] == rodaje["id"] for r in resp.json())

    def test_get_my_rodaje(self, client, rodaje_owner, rodaje):
        resp = client.get(f"/rodajes/me/{rodaje['id']}", headers=rodaje_owner)
        assert resp.status_code == 200
        assert resp.json()["id"] == rodaje["id"]

    def test_get_my_rodaje_not_found(self, client, rodaje_owner):
        resp = client.get("/rodajes/me/99999999", headers=rodaje_owner)
        assert resp.status_code == 404

    def test_get_other_user_is_404(self, client, user_headers, rodaje):
        # Otro usuario distinto del dueño no puede ver el rodaje (filtrado por user_id)
        resp = client.get(f"/rodajes/me/{rodaje['id']}", headers=user_headers)
        assert resp.status_code == 404

    def test_update_my_rodaje(self, client, rodaje_owner, rodaje):
        resp = client.put(
            f"/rodajes/me/{rodaje['id']}",
            headers=rodaje_owner,
            json={"titulo_produccion": "Actualizada"},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo_produccion"] == "Actualizada"

    def test_update_other_user_is_404(self, client, user_headers, rodaje):
        resp = client.put(
            f"/rodajes/me/{rodaje['id']}",
            headers=user_headers,
            json={"titulo_produccion": "Hack"},
        )
        assert resp.status_code == 404

    def test_delete_borrador(self, client, rodaje_owner, rodaje):
        resp = client.delete(f"/rodajes/me/{rodaje['id']}", headers=rodaje_owner)
        assert resp.status_code == 204

    def test_delete_non_borrador_is_400(self, client, rodaje_owner):
        # Regla de negocio: solo se pueden eliminar rodajes en borrador
        no_borrador = _crear_rodaje(client, rodaje_owner, borrador=False)
        resp = client.delete(
            f"/rodajes/me/{no_borrador['id']}", headers=rodaje_owner
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Rutas admin
# ---------------------------------------------------------------------------


class TestRodajeAdmin:
    def test_admin_list_all(self, client, admin_headers, rodaje):
        resp = client.get("/rodajes/admin/all", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_admin_list_forbidden_for_regular_user(self, client, user_headers):
        resp = client.get("/rodajes/admin/all", headers=user_headers)
        assert resp.status_code == 403

    def test_admin_get_by_id(self, client, admin_headers, rodaje):
        resp = client.get(f"/rodajes/admin/{rodaje['id']}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == rodaje["id"]

    def test_admin_get_forbidden_for_regular_user(self, client, user_headers, rodaje):
        resp = client.get(f"/rodajes/admin/{rodaje['id']}", headers=user_headers)
        assert resp.status_code == 403

    def test_admin_get_not_found(self, client, admin_headers):
        resp = client.get("/rodajes/admin/99999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_admin_update_estado(self, client, admin_headers, rodaje):
        resp = client.put(
            f"/rodajes/admin/{rodaje['id']}",
            headers=admin_headers,
            json={"estado_tramite": "aprobado", "inspector_asignado": "Insp. Test"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado_tramite"] == "aprobado"

    def test_admin_delete(self, client, admin_headers, rodaje):
        resp = client.delete(f"/rodajes/admin/{rodaje['id']}", headers=admin_headers)
        assert resp.status_code == 204

    def test_admin_stats(self, client, admin_headers, rodaje):
        resp = client.get("/rodajes/admin/stats/resumen", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert {"total", "por_estado", "por_tipo_produccion", "por_anio"}.issubset(
            body.keys()
        )

    def test_admin_stats_forbidden_for_regular_user(self, client, user_headers):
        resp = client.get("/rodajes/admin/stats/resumen", headers=user_headers)
        assert resp.status_code == 403
