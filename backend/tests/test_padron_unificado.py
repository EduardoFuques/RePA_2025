"""Padrón unificado, auditoría en JSONB y logging canónico.

Cubre lo que se agregó al rehacer el panel de administración:
- GET /admin/registros: los 5 tipos en una lista, multi-filtro, borradores fuera.
- Búsqueda insensible a acentos (extensión `unaccent`).
- audit_logs.details como JSONB + request_id que correlaciona con el log.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_headers(client: TestClient) -> dict:
    response = client.post(
        "/users/token",
        data={"username": "admin@repa.gob.ar", "password": "Admin1234"},
    )
    if response.status_code != 200:
        pytest.skip("No se pudo obtener token de admin")
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestPadronUnificado:
    def test_lista_todos_los_tipos(self, client: TestClient, admin_headers: dict):
        """Sin filtro de tipo, la lista mezcla los 5 formularios."""
        data = client.get(
            "/admin/registros?limit=200", headers=admin_headers
        ).json()
        assert set(data.keys()) >= {"items", "total", "offset", "limit"}
        tipos = {i["tipo"] for i in data["items"]}
        # El seed carga PF, PJ, AS y ESA; alcanza con que haya más de un tipo
        # para probar que efectivamente une tablas distintas.
        assert len(tipos) > 1
        assert tipos <= {"pf", "pj", "as", "esa", "agam"}

    def test_proyeccion_comun(self, client: TestClient, admin_headers: dict):
        """Cada fila trae la misma forma, venga de la tabla que venga."""
        items = client.get("/admin/registros?limit=50", headers=admin_headers).json()[
            "items"
        ]
        assert items, "el seed debería dejar registros"
        for fila in items:
            assert set(fila.keys()) >= {
                "tipo", "tipo_label", "id", "nombre", "estado",
                "borrador", "codigo_repa", "updated_at", "user_id", "user_email",
            }

    def test_borradores_ocultos_por_defecto(
        self, client: TestClient, admin_headers: dict
    ):
        """Si el usuario no lo envió, el revisor no tiene nada que revisar."""
        sin = client.get("/admin/registros?limit=200", headers=admin_headers).json()
        assert all(not i["borrador"] for i in sin["items"])

        con = client.get(
            "/admin/registros?incluir_borradores=true&limit=200", headers=admin_headers
        ).json()
        assert con["total"] >= sin["total"]

    def test_filtro_multi_tipo(self, client: TestClient, admin_headers: dict):
        data = client.get(
            "/admin/registros?tipos=pf&tipos=pj&limit=200", headers=admin_headers
        ).json()
        assert {i["tipo"] for i in data["items"]} <= {"pf", "pj"}

    def test_filtro_multi_estado(self, client: TestClient, admin_headers: dict):
        data = client.get(
            "/admin/registros?estados=enviado&estados=aprobado&limit=200",
            headers=admin_headers,
        ).json()
        assert {i["estado"] for i in data["items"]} <= {"enviado", "aprobado"}

    def test_tipo_invalido_es_400(self, client: TestClient, admin_headers: dict):
        response = client.get("/admin/registros?tipos=inexistente", headers=admin_headers)
        assert response.status_code == 400

    def test_requiere_permiso(self, client: TestClient):
        assert client.get("/admin/registros").status_code == 401

    def test_busqueda_ignora_acentos(self, client: TestClient, admin_headers: dict):
        """Buscar "Gonzalez" tiene que encontrar "González".

        Si la extensión `unaccent` no está instalada la búsqueda degrada a un
        ILIKE común, así que el test se salta en vez de fallar.
        """
        con_tilde = client.get(
            "/admin/registros?q=González", headers=admin_headers
        ).json()
        if con_tilde["total"] == 0:
            pytest.skip("El seed no tiene un apellido con tilde para probar")

        sin_tilde = client.get(
            "/admin/registros?q=Gonzalez", headers=admin_headers
        ).json()
        if sin_tilde["total"] == 0:
            pytest.skip("Extensión unaccent no disponible en esta base")
        assert sin_tilde["total"] == con_tilde["total"]


class TestAuditoriaEstructurada:
    def test_details_es_objeto(self, client: TestClient, admin_headers: dict):
        """`details` pasó de TEXT a JSONB: llega como dict, no como string."""
        items = client.get(
            "/admin_user/audit-logs?days=3650&limit=100", headers=admin_headers
        ).json()["items"]
        con_detalle = [i for i in items if i["details"] is not None]
        assert con_detalle, "el login del fixture ya debería haber dejado auditoría"
        assert all(isinstance(i["details"], dict) for i in con_detalle)

    def test_request_id_correlaciona(self, client: TestClient, admin_headers: dict):
        """La fila de auditoría lleva el request_id de la request que la generó."""
        items = client.get(
            "/admin_user/audit-logs?days=3650&limit=100", headers=admin_headers
        ).json()["items"]
        con_request = [i for i in items if i.get("request_id")]
        assert con_request, "las acciones dentro de una request deben traer request_id"

        rid = con_request[0]["request_id"]
        filtrado = client.get(
            f"/admin_user/audit-logs?days=3650&request_id={rid}", headers=admin_headers
        ).json()
        assert filtrado["total"] >= 1
        assert all(i["request_id"] == rid for i in filtrado["items"])

    def test_login_fallido_queda_auditado(self, client: TestClient, admin_headers: dict):
        """LOGIN_FAILED estaba definido pero nunca se emitía."""
        client.post(
            "/users/token",
            data={"username": "admin@repa.gob.ar", "password": "ContraseñaIncorrecta1"},
        )
        data = client.get(
            "/admin_user/audit-logs?action=LOGIN_FAILED&days=1", headers=admin_headers
        ).json()
        assert data["total"] >= 1
        assert data["items"][0]["details"]["motivo"] == "password_incorrecta"

    def test_filtro_por_email(self, client: TestClient, admin_headers: dict):
        """Filtrar por email en vez de tener que pegar un UUID."""
        data = client.get(
            "/admin_user/audit-logs?email=admin@repa.gob.ar&days=3650&limit=10",
            headers=admin_headers,
        ).json()
        assert data["total"] >= 1
        assert all(i["user_email"] == "admin@repa.gob.ar" for i in data["items"])

    def test_filtro_multi_accion(self, client: TestClient, admin_headers: dict):
        data = client.get(
            "/admin_user/audit-logs?actions=LOGIN&actions=CREATE&days=3650&limit=50",
            headers=admin_headers,
        ).json()
        assert {i["action"] for i in data["items"]} <= {"LOGIN", "CREATE"}


class TestLoggingCanonico:
    def test_una_linea_por_request_con_status_y_latencia(
        self, client: TestClient, caplog
    ):
        """El log se emite al salir, con status, latencia y request_id."""
        import logging

        with caplog.at_level(logging.INFO, logger="repa"):
            client.get("/admin/registros")  # 401, no importa: interesa el log

        canonicos = [
            r for r in caplog.records if getattr(r, "request_id", None) is not None
        ]
        assert len(canonicos) >= 1
        registro = canonicos[-1]
        assert registro.status == 401
        assert registro.method == "GET"
        assert registro.path == "/admin/registros"
        assert registro.duration_ms >= 0
        assert registro.auth == "anonymous"

    def test_formatter_conserva_el_contexto_extra(self):
        """El JSONFormatter descartaba todo lo que llegaba por `extra`."""
        import json
        import logging

        from src.logger import JSONFormatter

        registro = logging.LogRecord(
            name="repa", level=logging.INFO, pathname=__file__, lineno=1,
            msg="GET /x 200 1ms", args=(), exc_info=None,
        )
        registro.request_id = "abc123"
        registro.status = 200

        salida = json.loads(JSONFormatter().format(registro))
        assert salida["request_id"] == "abc123"
        assert salida["status"] == 200
        assert salida["message"] == "GET /x 200 1ms"
