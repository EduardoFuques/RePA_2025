# tests/test_expediente.py
"""Tests del módulo de Expedientes Administrativos (Administración General).

Matriz cubierta:

| Caso                                   | Esperado |
| -------------------------------------- | -------- |
| POST happy path (admin)                | 201      |
| GET por id (admin)                     | 200      |
| PUT parcial (admin)                    | 200      |
| DELETE (admin)                         | 204      |
| Cualquier endpoint sin Authorization   | 401      |
| POST/GET/PUT/DELETE con rol 'user'     | 403      |
| GET / PUT / DELETE de un id inexistente| 404      |
| Listado con filtros estado/area/anio/tipo y paginación | 200 + subconjunto |
| GET stats/resumen (indicadores)        | 200      |

Nota: los tests dependen de que el router esté montado en main.py y de que
`expedientes:manage` exista en rbac.py (el rol admin recibe todos los
permisos del catálogo). La ruta base se resuelve desde la app y no se
hardcodea, para no acoplar la suite al prefix elegido al montar el router.

No se importa `src.*` a nivel de módulo: conftest levanta el contenedor de
Postgres al importarse y los imports tienen que ocurrir después.
"""

import uuid

import pytest


def _base(client):
    """Prefix real del router, leído de la app (ver nota del docstring).

    Por nombre de endpoint y no recorriendo `app.routes`: desde FastAPI 0.141
    los routers incluidos quedan anidados (`_IncludedRouter`) y ya no aparecen
    aplanados ahí. Antes esto recorría la lista, no encontraba nada y hacía
    `pytest.skip` — la suite entera se salteaba en silencio. Si el router no
    está montado, que falle: un skip escondería exactamente ese error.
    """
    return client.app.url_path_for("listar_expedientes").rstrip("/")


def _nuevo_expediente(**overrides):
    """Payload válido mínimo; los overrides permiten variar area/tipo/año."""
    data = {
        # Sufijo aleatorio: la suite comparte la base entre tests y el número
        # provincial se usa para identificar las filas propias de cada test.
        "numero_expediente_provincial": f"EXP-{uuid.uuid4().hex[:8]}",
        "fecha_alta": "2025-03-10",
        "tipo_expediente": "apoyo_directo",
        "area_solicitante": "fomento",
        "nombre_proyecto": "Ciclo de cine itinerante",
        "codigo_repa": "PF-0001",
        "resolucion_id": "123/2025",
        "resolucion_pdf_path": "uploads/documents/resolucion-123-2025.pdf",
        "estado_expediente": "iniciado",
        "monto_solicitado": "1000000.00",
        "monto_aprobado": "800000.00",
        "monto_ejecutado": "400000.00",
        "fuente_presupuestaria": "presupuesto_iaavim",
        "forma_pago": "transferencia",
        "genera_informe_financiero": "en_evaluacion",
        "genera_devolucion": True,
        "observaciones_administrativas": "Pago en dos cuotas",
    }
    data.update(overrides)
    return data


@pytest.fixture
def crear_expediente(client, admin_headers):
    """Factory: crea un expediente vía API y devuelve el JSON creado."""

    def _factory(**overrides):
        resp = client.post(
            f"{_base(client)}/", json=_nuevo_expediente(**overrides),
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _factory


class TestExpedienteCRUD:
    """Happy path del CRUD con un usuario que tiene expedientes:manage."""

    def test_crear_expediente(self, client, admin_headers):
        payload = _nuevo_expediente()
        resp = client.post(f"{_base(client)}/", json=payload, headers=admin_headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["id"] > 0  # identificador propio incremental
        assert data["numero_expediente_provincial"] == (
            payload["numero_expediente_provincial"]
        )
        assert data["area_solicitante"] == "fomento"
        assert data["resolucion_pdf_path"] == payload["resolucion_pdf_path"]
        assert float(data["monto_aprobado"]) == 800000.00

    def test_obtener_expediente(self, client, admin_headers, crear_expediente):
        creado = crear_expediente()
        resp = client.get(f"{_base(client)}/{creado['id']}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == creado["id"]

    def test_actualizar_expediente_es_parcial(
        self, client, admin_headers, crear_expediente
    ):
        """Un PUT con un solo campo no debe pisar el resto del expediente."""
        creado = crear_expediente()
        resp = client.put(
            f"{_base(client)}/{creado['id']}",
            json={"estado_expediente": "pagado", "monto_ejecutado": "800000.00"},
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["estado_expediente"] == "pagado"
        assert float(data["monto_ejecutado"]) == 800000.00
        assert data["nombre_proyecto"] == creado["nombre_proyecto"]

    def test_eliminar_un_borrador(self, client, admin_headers, crear_expediente):
        creado = crear_expediente(borrador=True)
        resp = client.delete(f"{_base(client)}/{creado['id']}", headers=admin_headers)
        assert resp.status_code == 204
        assert (
            client.get(
                f"{_base(client)}/{creado['id']}", headers=admin_headers
            ).status_code
            == 404
        )


class TestExpedienteNotFound:
    """404 sobre un id inexistente (no 500 ni 200 vacío)."""

    ID_INEXISTENTE = 99999999

    def test_get_inexistente(self, client, admin_headers):
        resp = client.get(
            f"{_base(client)}/{self.ID_INEXISTENTE}", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_put_inexistente(self, client, admin_headers):
        resp = client.put(
            f"{_base(client)}/{self.ID_INEXISTENTE}",
            json={"estado_expediente": "pagado"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_no_se_elimina_un_expediente_cargado(
        self, client, admin_headers, crear_expediente
    ):
        # Queda en el historial de ejecucion presupuestaria: solo los
        # borradores (cargas a medio hacer) se pueden eliminar.
        creado = crear_expediente()
        resp = client.delete(f"{_base(client)}/{creado['id']}", headers=admin_headers)
        assert resp.status_code == 409
        assert "borradores" in resp.json()["detail"]
        assert client.get(
            f"{_base(client)}/{creado['id']}", headers=admin_headers
        ).status_code == 200

    def test_delete_inexistente(self, client, admin_headers):
        resp = client.delete(
            f"{_base(client)}/{self.ID_INEXISTENTE}", headers=admin_headers
        )
        assert resp.status_code == 404


class TestExpedientePermisos:
    """El módulo es interno: sin token 401, con rol 'user' 403."""

    def test_sin_autenticacion(self, client):
        base = _base(client)
        assert client.get(f"{base}/").status_code == 401
        assert client.post(f"{base}/", json=_nuevo_expediente()).status_code == 401
        assert client.get(f"{base}/stats/resumen").status_code == 401

    def test_rol_user_sin_permiso(self, client, user_headers, crear_expediente):
        base = _base(client)
        creado = crear_expediente()
        assert (
            client.post(
                f"{base}/", json=_nuevo_expediente(), headers=user_headers
            ).status_code
            == 403
        )
        assert client.get(f"{base}/", headers=user_headers).status_code == 403
        assert (
            client.get(f"{base}/{creado['id']}", headers=user_headers).status_code
            == 403
        )
        assert (
            client.put(
                f"{base}/{creado['id']}",
                json={"estado_expediente": "pagado"},
                headers=user_headers,
            ).status_code
            == 403
        )
        assert (
            client.delete(f"{base}/{creado['id']}", headers=user_headers).status_code
            == 403
        )
        assert client.get(f"{base}/stats/resumen", headers=user_headers).status_code == 403

    def test_usuario_creado_ad_hoc_sin_rol(self, client, create_user):
        """Un usuario sin roles tampoco entra (no alcanza con estar logueado)."""
        _, headers = create_user(f"expediente_{uuid.uuid4().hex[:8]}@example.com")
        assert client.get(f"{_base(client)}/", headers=headers).status_code == 403


class TestExpedienteListado:
    """Filtros y paginación del listado de backoffice."""

    def test_listado_estructura_y_paginacion(
        self, client, admin_headers, crear_expediente
    ):
        crear_expediente()
        crear_expediente()
        resp = client.get(f"{_base(client)}/?limit=1", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(data) == {"items", "total", "offset", "limit"}
        assert len(data["items"]) == 1
        # total cuenta todo lo que matchea el filtro, no solo la página.
        assert data["total"] >= 2
        assert data["offset"] == 0 and data["limit"] == 1

    def test_filtro_por_estado(self, client, admin_headers, crear_expediente):
        crear_expediente(estado_expediente="en_tesoreria")
        resp = client.get(
            f"{_base(client)}/?estado=en_tesoreria", headers=admin_headers
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items
        assert all(i["estado_expediente"] == "en_tesoreria" for i in items)

    def test_filtro_por_area(self, client, admin_headers, crear_expediente):
        crear_expediente(area_solicitante="cinemateca")
        resp = client.get(f"{_base(client)}/?area=cinemateca", headers=admin_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items
        assert all(i["area_solicitante"] == "cinemateca" for i in items)

    def test_filtro_por_tipo(self, client, admin_headers, crear_expediente):
        crear_expediente(tipo_expediente="convenio_terceros")
        resp = client.get(
            f"{_base(client)}/?tipo_expediente=convenio_terceros",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items
        assert all(i["tipo_expediente"] == "convenio_terceros" for i in items)

    def test_filtro_por_anio(self, client, admin_headers, crear_expediente):
        """El filtro `anio` mira el año de fecha_alta, no el de creación."""
        creado = crear_expediente(fecha_alta="2019-07-01")
        resp = client.get(f"{_base(client)}/?anio=2019", headers=admin_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert creado["id"] in [i["id"] for i in items]
        assert all(i["fecha_alta"].startswith("2019") for i in items)

    def test_filtros_combinados_excluyentes(
        self, client, admin_headers, crear_expediente
    ):
        """Filtros que no matchean juntos devuelven una página vacía, no 404."""
        crear_expediente(area_solicitante="juridico", fecha_alta="2018-01-05")
        resp = client.get(
            f"{_base(client)}/?area=juridico&anio=1999", headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []


class TestExpedienteResumen:
    """Indicadores agregados pedidos por el formulario del área."""

    def test_resumen_devuelve_indicadores(
        self, client, admin_headers, crear_expediente
    ):
        crear_expediente(
            area_solicitante="capacitacion",
            fecha_alta="2021-05-05",
            tipo_expediente="pago_capacitadores",
            monto_aprobado="1000.00",
            monto_ejecutado="500.00",
        )
        resp = client.get(f"{_base(client)}/stats/resumen", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "ejecucion_por_area_anio" in data
        assert "por_tipo_expediente" in data

        fila = next(
            f
            for f in data["ejecucion_por_area_anio"]
            if f["area_solicitante"] == "capacitacion" and f["anio"] == 2021
        )
        assert fila["porcentaje_ejecucion"] == 50.0

        tipo = next(
            t
            for t in data["por_tipo_expediente"]
            if t["tipo_expediente"] == "pago_capacitadores"
        )
        assert tipo["cantidad"] >= 1
        assert float(tipo["monto_aprobado"]) >= 1000.00


class TestExpedienteResolucionPdf:
    """Mismo criterio que los adjuntos del digesto: se sirve el PDF que subio
    otro gestor, pero solo si la ruta tiene el formato de su tipo de upload."""

    @pytest.fixture
    def uploads(self, tmp_path, monkeypatch):
        import src.routes.upload_routes as upload_routes

        monkeypatch.setattr(upload_routes, "UPLOAD_BASE_DIR", str(tmp_path))
        return tmp_path

    def _archivo(self, uploads, user_id, nombre):
        carpeta = uploads / user_id
        carpeta.mkdir(exist_ok=True)
        (carpeta / nombre).write_bytes(b"%PDF-1.4 prueba")
        return f"{user_id}/{nombre}"

    def test_descarga_la_resolucion(self, client, admin_headers, crear_expediente, uploads):
        ruta = self._archivo(uploads, "otro-gestor", "expediente_resolucion_abc.pdf")
        exp = crear_expediente(resolucion_pdf_path=ruta)
        resp = client.get(
            f"{_base(client)}/{exp['id']}/resolucion-pdf", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.content.startswith(b"%PDF")

    def test_no_sirve_un_archivo_de_otro_tipo(
        self, client, admin_headers, crear_expediente, uploads
    ):
        ruta = self._archivo(uploads, "victima", "dni_abc.pdf")
        exp = crear_expediente(resolucion_pdf_path=ruta)
        resp = client.get(
            f"{_base(client)}/{exp['id']}/resolucion-pdf", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_sin_pdf_es_404(self, client, admin_headers, crear_expediente):
        exp = crear_expediente(resolucion_pdf_path=None)
        resp = client.get(
            f"{_base(client)}/{exp['id']}/resolucion-pdf", headers=admin_headers
        )
        assert resp.status_code == 404

    def test_sin_permiso_es_403(self, client, user_headers, crear_expediente):
        exp = crear_expediente()
        resp = client.get(
            f"{_base(client)}/{exp['id']}/resolucion-pdf", headers=user_headers
        )
        assert resp.status_code == 403
