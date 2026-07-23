"""
Tests de mass assignment: un solicitante NO debe poder escribir campos
administrativos de su propio expediente (autoaprobación de subsidios en
Fomento, autoaprobación del permiso de filmación en Rodaje).

Los campos administrativos solo se aceptan vía los schemas *AdminUpdate en
las rutas admin, que además dejan rastro en el audit trail.
"""

import uuid

import pytest


@pytest.fixture
def fresh_user(create_user):
    """Usuario regular fresco (un trámite por usuario → /me determinista)."""
    _user, headers = create_user(
        f"massasg_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
    )
    return headers


# ---------------------------------------------------------------------------
# FOMENTO — Trámite
# ---------------------------------------------------------------------------


class TestTramiteMassAssignment:
    PAYLOAD_MALICIOSO = {
        "titulo_proyecto": "Proyecto X",
        "estado_tramite": "aprobado",
        "monto_aprobado_iaavim": 99999999,
        "nro_expediente": "EXP-FALSO-001",
        "rendicion_estado": "aprobada",
        "convenio_path": "/tmp/convenio_falso.pdf",
        "resolucion_otorgamiento_path": "/tmp/resolucion_falsa.pdf",
        "pendiente_juridico": True,
    }

    def test_create_ignora_campos_admin(self, client, fresh_user):
        resp = client.post(
            "/fomento/tramites", headers=fresh_user, json=self.PAYLOAD_MALICIOSO
        )
        assert resp.status_code == 201, resp.text
        tramite = resp.json()
        assert tramite["titulo_proyecto"] == "Proyecto X"
        assert tramite["estado_tramite"] is None
        assert tramite["monto_aprobado_iaavim"] is None
        assert tramite["nro_expediente"] is None
        assert tramite["rendicion_estado"] is None
        assert tramite["convenio_path"] is None
        assert tramite["resolucion_otorgamiento_path"] is None
        assert tramite["pendiente_juridico"] is False

    def test_update_me_ignora_campos_admin(self, client, fresh_user):
        client.post(
            "/fomento/tramites",
            headers=fresh_user,
            json={"titulo_proyecto": "Original"},
        )
        resp = client.put(
            "/fomento/tramites/me", headers=fresh_user, json=self.PAYLOAD_MALICIOSO
        )
        assert resp.status_code == 200, resp.text
        tramite = resp.json()
        # El campo legítimo sí se actualiza; los administrativos no.
        assert tramite["titulo_proyecto"] == "Proyecto X"
        assert tramite["estado_tramite"] is None
        assert tramite["monto_aprobado_iaavim"] is None
        assert tramite["nro_expediente"] is None

    def test_update_por_id_ignora_campos_admin(self, client, fresh_user):
        create = client.post(
            "/fomento/tramites",
            headers=fresh_user,
            json={"titulo_proyecto": "Original"},
        )
        tramite_id = create.json()["id"]
        resp = client.put(
            f"/fomento/tramites/{tramite_id}",
            headers=fresh_user,
            json=self.PAYLOAD_MALICIOSO,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["estado_tramite"] is None
        assert resp.json()["monto_aprobado_iaavim"] is None

    def test_admin_route_forbidden_para_usuario(self, client, fresh_user):
        create = client.post(
            "/fomento/tramites",
            headers=fresh_user,
            json={"titulo_proyecto": "Original"},
        )
        tramite_id = create.json()["id"]
        resp = client.put(
            f"/fomento/tramites/{tramite_id}/admin",
            headers=fresh_user,
            json={"estado_tramite": "aprobado"},
        )
        assert resp.status_code == 403

    def test_admin_route_aplica_campos_admin(
        self, client, fresh_user, admin_headers
    ):
        create = client.post(
            "/fomento/tramites",
            headers=fresh_user,
            json={"titulo_proyecto": "Original"},
        )
        tramite_id = create.json()["id"]
        resp = client.put(
            f"/fomento/tramites/{tramite_id}/admin",
            headers=admin_headers,
            json={
                "estado_tramite": "aprobado",
                "monto_aprobado_iaavim": 500000,
                "nro_expediente": "EXP-2026-001",
            },
        )
        assert resp.status_code == 200, resp.text
        tramite = resp.json()
        assert tramite["estado_tramite"] == "aprobado"
        assert tramite["monto_aprobado_iaavim"] == 500000
        assert tramite["nro_expediente"] == "EXP-2026-001"

    def test_admin_update_queda_auditado(self, client, fresh_user, admin_headers):
        create = client.post(
            "/fomento/tramites",
            headers=fresh_user,
            json={"titulo_proyecto": "Auditable"},
        )
        tramite_id = create.json()["id"]
        client.put(
            f"/fomento/tramites/{tramite_id}/admin",
            headers=admin_headers,
            json={"estado_tramite": "aprobado"},
        )
        logs = client.get(
            "/admin_user/audit-logs",
            headers=admin_headers,
            params={"action": "UPDATE"},
        )
        assert logs.status_code == 200, logs.text
        items = logs.json()["items"]
        assert any(
            log["resource_type"] == "TramiteFomento"
            and log["resource_id"] == str(tramite_id)
            for log in items
        ), "El cambio admin de trámite no quedó en el audit trail"


# ---------------------------------------------------------------------------
# RODAJE
# ---------------------------------------------------------------------------


class TestRodajeMassAssignment:
    PAYLOAD_MALICIOSO = {
        "titulo_produccion": "Film X",
        "estado_tramite": "aprobado",
        "inspector_asignado": "Inspector Falso",
        "informe_inspeccion": "todo ok",
        "pagos_realizados": "pagado total",
        "observaciones_internas": "hackeado",
    }

    def test_create_ignora_campos_seguimiento(self, client, fresh_user):
        resp = client.post(
            "/rodajes/", headers=fresh_user, json=self.PAYLOAD_MALICIOSO
        )
        assert resp.status_code == 201, resp.text
        rodaje = resp.json()
        assert rodaje["titulo_produccion"] == "Film X"
        # estado_tramite cae al default del modelo, no al valor inyectado
        assert rodaje["estado_tramite"] == "recibido"
        assert rodaje["inspector_asignado"] is None
        assert rodaje["informe_inspeccion"] is None
        assert rodaje["pagos_realizados"] is None
        assert rodaje["observaciones_internas"] is None

    def test_update_me_ignora_campos_seguimiento(self, client, fresh_user):
        create = client.post(
            "/rodajes/", headers=fresh_user, json={"titulo_produccion": "Original"}
        )
        rodaje_id = create.json()["id"]
        resp = client.put(
            f"/rodajes/me/{rodaje_id}", headers=fresh_user, json=self.PAYLOAD_MALICIOSO
        )
        assert resp.status_code == 200, resp.text
        rodaje = resp.json()
        assert rodaje["titulo_produccion"] == "Film X"
        assert rodaje["estado_tramite"] == "recibido"
        assert rodaje["inspector_asignado"] is None

    def test_admin_route_aplica_campos_seguimiento(
        self, client, fresh_user, admin_headers
    ):
        create = client.post(
            "/rodajes/", headers=fresh_user, json={"titulo_produccion": "Original"}
        )
        rodaje_id = create.json()["id"]
        resp = client.put(
            f"/rodajes/admin/{rodaje_id}",
            headers=admin_headers,
            json={"estado_tramite": "aprobado", "inspector_asignado": "Inspector Real"},
        )
        assert resp.status_code == 200, resp.text
        rodaje = resp.json()
        assert rodaje["estado_tramite"] == "aprobado"
        assert rodaje["inspector_asignado"] == "Inspector Real"
