# tests/test_fomento_relacional.py
"""Tests para las relaciones 1:N de Fomento que reemplazaron el JSON suelto:
`TramiteFomento.pagos`/`otros_aportes_no_iaavim` y `ComiteFomento.integrantes`.

Fixtures compartidas: ver test_fomento.py (tramite, tramite_owner, evento,
evaluador, admin_headers, create_user).
"""
import pytest

from tests.test_fomento import (  # noqa: F401 — reexpone las fixtures compartidas
    evaluador,
    evaluador_owner,
    evento,
    linea,
    second_user,
    tramite,
    tramite_owner,
)


class TestAportesTramite:
    def test_create_tramite_con_aportes_persiste_filas(self, client, tramite_owner):
        resp = client.post(
            "/fomento/tramites",
            headers=tramite_owner,
            json={
                "titulo_proyecto": "Proyecto con aportes",
                "otros_aportes_no_iaavim": [
                    {"organismo": "INCAA", "programa": "Fomento", "monto": 100000, "moneda": "ARS"},
                    {"organismo": "Municipio", "programa": None, "monto": 50000, "moneda": "ARS"},
                ],
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert len(data["otros_aportes_no_iaavim"]) == 2
        organismos = {a["organismo"] for a in data["otros_aportes_no_iaavim"]}
        assert organismos == {"INCAA", "Municipio"}

    def test_update_aportes_reemplaza_todas_las_filas(self, client, tramite_owner, tramite):
        primero = client.put(
            "/fomento/tramites/me",
            headers=tramite_owner,
            json={"otros_aportes_no_iaavim": [
                {"organismo": "A", "monto": 1, "moneda": "ARS"},
                {"organismo": "B", "monto": 2, "moneda": "ARS"},
            ]},
        )
        assert primero.status_code == 200, primero.text
        assert len(primero.json()["otros_aportes_no_iaavim"]) == 2

        segundo = client.put(
            "/fomento/tramites/me",
            headers=tramite_owner,
            json={"otros_aportes_no_iaavim": [{"organismo": "C", "monto": 3, "moneda": "ARS"}]},
        )
        assert segundo.status_code == 200, segundo.text
        aportes = segundo.json()["otros_aportes_no_iaavim"]
        assert len(aportes) == 1
        assert aportes[0]["organismo"] == "C"

    def test_omitir_aportes_en_update_no_toca_los_existentes(self, client, tramite_owner):
        create = client.post(
            "/fomento/tramites",
            headers=tramite_owner,
            json={
                "titulo_proyecto": "X",
                "otros_aportes_no_iaavim": [{"organismo": "A", "monto": 1, "moneda": "ARS"}],
            },
        )
        assert create.status_code == 201, create.text

        update = client.put(
            "/fomento/tramites/me", headers=tramite_owner, json={"titulo_proyecto": "Y"}
        )
        assert update.status_code == 200, update.text
        assert len(update.json()["otros_aportes_no_iaavim"]) == 1

    def test_aporte_con_tipo_invalido_rechazado_422(self, client, tramite_owner):
        resp = client.post(
            "/fomento/tramites",
            headers=tramite_owner,
            json={
                "titulo_proyecto": "Z",
                "otros_aportes_no_iaavim": [{"organismo": "A", "monto": "no-es-un-numero"}],
            },
        )
        assert resp.status_code == 422


class TestPagosTramiteAdmin:
    def test_admin_puede_setear_pagos_via_endpoint_admin(self, client, admin_headers, tramite):
        resp = client.put(
            f"/fomento/tramites/{tramite['id']}/admin",
            headers=admin_headers,
            json={"pagos": [
                {"fecha": "2026-01-15T00:00:00", "monto": 50000, "moneda": "ARS", "concepto": "Anticipo"},
            ]},
        )
        assert resp.status_code == 200, resp.text
        pagos = resp.json()["pagos"]
        assert len(pagos) == 1
        assert pagos[0]["concepto"] == "Anticipo"

    def test_solicitante_no_puede_colar_pagos_via_create(self, client, tramite_owner):
        resp = client.post(
            "/fomento/tramites",
            headers=tramite_owner,
            json={
                "titulo_proyecto": "Fraude",
                "pagos": [{"monto": 999999, "concepto": "fraude"}],
            },
        )
        assert resp.status_code == 201, resp.text
        # El campo no existe en el schema de creación del solicitante — Pydantic
        # lo ignora silenciosamente (extra="ignore" es el default), y la
        # respuesta no debe traer ningún pago creado a partir de eso.
        assert resp.json()["pagos"] == []

    def test_solicitante_no_puede_colar_pagos_via_update_me(self, client, tramite_owner, tramite):
        resp = client.put(
            "/fomento/tramites/me",
            headers=tramite_owner,
            json={"pagos": [{"monto": 999999, "concepto": "fraude"}]},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["pagos"] == []

    def test_pago_con_tipo_invalido_rechazado_422(self, client, admin_headers, tramite):
        resp = client.put(
            f"/fomento/tramites/{tramite['id']}/admin",
            headers=admin_headers,
            json={"pagos": [{"monto": "no-es-un-numero"}]},
        )
        assert resp.status_code == 422


class TestIntegrantesComite:
    def _crear_comite(self, client, admin_headers, evento):
        resp = client.post(
            "/fomento/comites",
            headers=admin_headers,
            json={"evento_id": evento["id"], "tipo": "tecnico", "nombre": "Comité relacional"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_crear_comite_con_integrante_valido(self, client, admin_headers, evento, evaluador):
        comite = self._crear_comite(client, admin_headers, evento)
        resp = client.put(
            f"/fomento/comites/{comite['id']}",
            headers=admin_headers,
            json={"integrantes": [{"evaluador_id": evaluador["id"], "rol": "vocal"}]},
        )
        assert resp.status_code == 200, resp.text
        integrantes = resp.json()["integrantes"]
        assert len(integrantes) == 1
        assert integrantes[0]["evaluador_id"] == evaluador["id"]
        assert integrantes[0]["rol"] == "vocal"

    def test_evaluador_id_invalido_rechaza_el_lote_completo(
        self, client, admin_headers, evento, evaluador
    ):
        comite = self._crear_comite(client, admin_headers, evento)
        resp = client.put(
            f"/fomento/comites/{comite['id']}",
            headers=admin_headers,
            json={"integrantes": [
                {"evaluador_id": evaluador["id"], "rol": "presidente"},
                {"evaluador_id": 999999999, "rol": "vocal"},
            ]},
        )
        assert resp.status_code == 404

        # El integrante válido tampoco debe haber quedado aplicado (todo o nada).
        get = client.get(f"/fomento/comites/{comite['id']}", headers=admin_headers)
        assert get.status_code == 200
        assert get.json()["integrantes"] == []

    def test_update_integrantes_reemplaza_todas_las_filas(
        self, client, admin_headers, evento, evaluador
    ):
        comite = self._crear_comite(client, admin_headers, evento)
        primero = client.put(
            f"/fomento/comites/{comite['id']}",
            headers=admin_headers,
            json={"integrantes": [{"evaluador_id": evaluador["id"], "rol": "vocal"}]},
        )
        assert primero.status_code == 200
        assert len(primero.json()["integrantes"]) == 1

        segundo = client.put(
            f"/fomento/comites/{comite['id']}",
            headers=admin_headers,
            json={"integrantes": []},
        )
        assert segundo.status_code == 200
        assert segundo.json()["integrantes"] == []
