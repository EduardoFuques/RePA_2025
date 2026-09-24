"""
Tests del módulo de Instrumentos Jurídicos (Digesto Jurídico Institucional).

Matriz por endpoint: happy path + autenticación (401) + autorización
(403 con rol 'user', porque todo el módulo exige instrumentos:manage)
+ 404 de recursos + bloque condicional del acta del Consejo Directivo
+ filtros del listado paginado + informe de resumen.

Fixtures compartidas (conftest.py): client, admin_headers, user_headers, create_user.

NOTA: nada de `import src.*` a nivel de módulo — conftest levanta el contenedor
de Postgres y fija DATABASE_URL antes de recolectar, pero igual se importa
dentro de los tests para no depender del orden.
"""
import uuid

import pytest

BASE = "/instrumentos-juridicos"


def _payload(**extra):
    """Payload mínimo válido: tipo, título, resumen y adjunto son obligatorios."""
    payload = {
        "tipo_documento": "resolucion",
        "numero_instrumento": f"RES-{uuid.uuid4().hex[:8]}",
        "titulo": "Resolución de prueba",
        "resumen": "Extracto del contenido de la resolución de prueba.",
        "archivo_pdf_path": "uploads/instrumentos/res-test.pdf",
        "fecha_emision": "2025-03-10",
    }
    payload.update(extra)
    return payload


def _crear(client, headers, **extra):
    resp = client.post(f"{BASE}/", headers=headers, json=_payload(**extra))
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def juridico_headers(create_user):
    """Usuario del área jurídica: se usa 'admin' porque hereda todos los permisos."""
    _user, headers = create_user(
        f"juridico_{uuid.uuid4().hex[:8]}@example.com", roles=["admin"]
    )
    return headers


@pytest.fixture
def instrumento(client, juridico_headers):
    """Instrumento simple (resolución) ya cargado en el digesto."""
    return _crear(client, juridico_headers)


# ---------------------------------------------------------------------------
# Alta
# ---------------------------------------------------------------------------


class TestInstrumentoCreate:
    def test_create_requires_auth(self, client):
        resp = client.post(f"{BASE}/", json=_payload())
        assert resp.status_code == 401

    def test_create_forbidden_for_regular_user(self, client, user_headers):
        # El digesto es de uso interno del área: el rol 'user' no entra.
        resp = client.post(f"{BASE}/", headers=user_headers, json=_payload())
        assert resp.status_code == 403

    def test_create_happy_path(self, client, instrumento):
        assert instrumento["id"]
        assert instrumento["tipo_documento"] == "resolucion"
        assert instrumento["usuario_carga_id"]
        # Campo automático de la sección 7
        assert instrumento["estado_revision"] == "en_revision"
        assert instrumento["acta"] is None

    def test_create_validacion_campos_obligatorios(self, client, juridico_headers):
        # Sin resumen ni archivo adjunto -> 422 de Pydantic
        resp = client.post(
            f"{BASE}/",
            headers=juridico_headers,
            json={"tipo_documento": "resolucion", "titulo": "Sin resumen"},
        )
        assert resp.status_code == 422

    def test_create_con_campos_de_tematizacion_y_trazabilidad(
        self, client, juridico_headers
    ):
        creado = _crear(
            client,
            juridico_headers,
            tipo_documento="convenio_marco",
            ambito_aplicacion="provincial",
            tematica_principal="convenios_cooperacion",
            areas_vinculadas=["juridico", "gerencia_fomento"],
            palabras_clave=["convenio", "cooperacion"],
            condiciones_finalizacion=["aprobacion_rendicion_cuentas"],
            codigo_repa_vinculado="REPA-0001",
            proyecto_id="PROY-77",
            vinculado_resolucion_previa=True,
            resolucion_previa_id="RES-2024-15",
        )
        assert creado["areas_vinculadas"] == ["juridico", "gerencia_fomento"]
        assert creado["resolucion_previa_id"] == "RES-2024-15"
        assert creado["condiciones_finalizacion"] == ["aprobacion_rendicion_cuentas"]

    def test_palabras_clave_max_5(self, client, juridico_headers):
        resp = client.post(
            f"{BASE}/",
            headers=juridico_headers,
            json=_payload(palabras_clave=["a", "b", "c", "d", "e", "f"]),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Bloque condicional: Acta del Consejo Directivo (sección 4)
# ---------------------------------------------------------------------------


class TestActaConsejoDirectivo:
    def test_acta_se_crea_con_el_instrumento(self, client, juridico_headers):
        creado = _crear(
            client,
            juridico_headers,
            tipo_documento="acta_consejo_directivo",
            titulo="Acta CD 03/2025",
            acta={
                "fecha_reunion": "2025-03-05",
                "asistentes": [
                    {"nombre": "Juan Pérez", "cargo": "Presidente", "organizacion": "IAAviM"}
                ],
                "ordenes_del_dia": "1) Presupuesto 2) Convenios",
                "decisiones_tomadas": "Se aprueba el presupuesto.",
                "acta_pdf_path": "uploads/actas/acta-03-2025.pdf",
                "resoluciones_emitidas": ["RES-2025-40", "RES-2025-41"],
            },
        )
        acta = creado["acta"]
        assert acta is not None
        assert acta["instrumento_id"] == creado["id"]
        assert acta["fecha_reunion"] == "2025-03-05"
        assert acta["resoluciones_emitidas"] == ["RES-2025-40", "RES-2025-41"]
        assert acta["asistentes"][0]["cargo"] == "Presidente"

    def test_acta_rechazada_si_el_tipo_no_corresponde(self, client, juridico_headers):
        # El bloque solo aplica cuando el tipo es acta_consejo_directivo.
        resp = client.post(
            f"{BASE}/",
            headers=juridico_headers,
            json=_payload(tipo_documento="resolucion", acta={"fecha_reunion": "2025-01-01"}),
        )
        assert resp.status_code == 400

    def test_acta_se_actualiza_por_put(self, client, juridico_headers):
        creado = _crear(
            client,
            juridico_headers,
            tipo_documento="acta_consejo_directivo",
            acta={"decisiones_tomadas": "Borrador"},
        )
        resp = client.put(
            f"{BASE}/{creado['id']}",
            headers=juridico_headers,
            json={"acta": {"decisiones_tomadas": "Versión final"}},
        )
        assert resp.status_code == 200
        assert resp.json()["acta"]["decisiones_tomadas"] == "Versión final"

    def test_acta_se_puede_agregar_despues(self, client, juridico_headers):
        # Instrumento cargado como acta pero sin el bloque: se agrega luego.
        creado = _crear(client, juridico_headers, tipo_documento="acta_consejo_directivo")
        assert creado["acta"] is None
        resp = client.put(
            f"{BASE}/{creado['id']}",
            headers=juridico_headers,
            json={"acta": {"fecha_reunion": "2025-06-01"}},
        )
        assert resp.status_code == 200
        assert resp.json()["acta"]["fecha_reunion"] == "2025-06-01"

    def test_acta_se_borra_en_cascada(self, client, juridico_headers):
        creado = _crear(
            client,
            juridico_headers,
            tipo_documento="acta_consejo_directivo",
            acta={"ordenes_del_dia": "Temario"},
            borrador=True,
        )
        assert client.delete(
            f"{BASE}/{creado['id']}", headers=juridico_headers
        ).status_code == 204
        assert client.get(
            f"{BASE}/{creado['id']}", headers=juridico_headers
        ).status_code == 404


# ---------------------------------------------------------------------------
# Lectura, actualización y baja
# ---------------------------------------------------------------------------


class TestInstrumentoCRUD:
    def test_get_requires_auth(self, client, instrumento):
        resp = client.get(f"{BASE}/{instrumento['id']}")
        assert resp.status_code == 401

    def test_get_forbidden_for_regular_user(self, client, user_headers, instrumento):
        resp = client.get(f"{BASE}/{instrumento['id']}", headers=user_headers)
        assert resp.status_code == 403

    def test_get_happy_path(self, client, juridico_headers, instrumento):
        resp = client.get(f"{BASE}/{instrumento['id']}", headers=juridico_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == instrumento["id"]

    def test_get_not_found(self, client, juridico_headers):
        resp = client.get(f"{BASE}/99999999", headers=juridico_headers)
        assert resp.status_code == 404

    def test_update_happy_path(self, client, juridico_headers, instrumento):
        resp = client.put(
            f"{BASE}/{instrumento['id']}",
            headers=juridico_headers,
            json={"titulo": "Resolución corregida", "estado_revision": "validado"},
        )
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Resolución corregida"
        assert resp.json()["estado_revision"] == "validado"

    def test_update_not_found(self, client, juridico_headers):
        resp = client.put(
            f"{BASE}/99999999", headers=juridico_headers, json={"titulo": "X"}
        )
        assert resp.status_code == 404

    def test_update_forbidden_for_regular_user(
        self, client, user_headers, instrumento
    ):
        resp = client.put(
            f"{BASE}/{instrumento['id']}", headers=user_headers, json={"titulo": "X"}
        )
        assert resp.status_code == 403

    def test_delete_de_un_borrador(self, client, juridico_headers):
        borrador = _crear(client, juridico_headers, borrador=True)
        resp = client.delete(f"{BASE}/{borrador['id']}", headers=juridico_headers)
        assert resp.status_code == 204

    def test_no_se_elimina_un_instrumento_cargado(
        self, client, juridico_headers, instrumento
    ):
        # El digesto es un archivo: un instrumento cargado se retira
        # archivandolo, no borrandolo.
        resp = client.delete(f"{BASE}/{instrumento['id']}", headers=juridico_headers)
        assert resp.status_code == 409
        assert "Archivado" in resp.json()["detail"]
        assert client.get(
            f"{BASE}/{instrumento['id']}", headers=juridico_headers
        ).status_code == 200

    def test_delete_not_found(self, client, juridico_headers):
        resp = client.delete(f"{BASE}/99999999", headers=juridico_headers)
        assert resp.status_code == 404

    def test_delete_forbidden_for_regular_user(
        self, client, user_headers, instrumento
    ):
        resp = client.delete(f"{BASE}/{instrumento['id']}", headers=user_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Listado paginado y filtros de búsqueda
# ---------------------------------------------------------------------------


class TestInstrumentoListado:
    def test_list_requires_auth(self, client):
        assert client.get(f"{BASE}/").status_code == 401

    def test_list_forbidden_for_regular_user(self, client, user_headers):
        assert client.get(f"{BASE}/", headers=user_headers).status_code == 403

    def test_list_estructura_paginada(self, client, juridico_headers, instrumento):
        resp = client.get(f"{BASE}/", headers=juridico_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert {"items", "total", "offset", "limit"}.issubset(body.keys())
        assert body["limit"] == 50
        assert body["offset"] == 0

    def test_list_limit_maximo(self, client, juridico_headers):
        # limit > 200 -> 422 (Query(le=200))
        resp = client.get(f"{BASE}/?limit=500", headers=juridico_headers)
        assert resp.status_code == 422

    def test_filtro_por_numero(self, client, juridico_headers, instrumento):
        resp = client.get(
            f"{BASE}/",
            headers=juridico_headers,
            params={"numero_instrumento": instrumento["numero_instrumento"]},
        )
        assert resp.status_code == 200
        assert [i["id"] for i in resp.json()["items"]] == [instrumento["id"]]

    def test_filtro_por_tipo_y_anio(self, client, juridico_headers, instrumento):
        resp = client.get(
            f"{BASE}/",
            headers=juridico_headers,
            params={"tipo_documento": "resolucion", "anio": 2025},
        )
        assert resp.status_code == 200
        assert any(i["id"] == instrumento["id"] for i in resp.json()["items"])

    def test_filtro_por_anio_sin_resultados(self, client, juridico_headers, instrumento):
        resp = client.get(f"{BASE}/", headers=juridico_headers, params={"anio": 1990})
        assert resp.status_code == 200
        assert all(i["id"] != instrumento["id"] for i in resp.json()["items"])

    def test_filtro_por_area_vinculada(self, client, juridico_headers):
        creado = _crear(client, juridico_headers, areas_vinculadas=["agam", "cinemateca"])
        resp = client.get(
            f"{BASE}/", headers=juridico_headers, params={"area_vinculada": "cinemateca"}
        )
        assert resp.status_code == 200
        assert any(i["id"] == creado["id"] for i in resp.json()["items"])

    def test_filtro_por_tematica_y_ambito(self, client, juridico_headers):
        creado = _crear(
            client,
            juridico_headers,
            tematica_principal="regulacion_normativa",
            ambito_aplicacion="nacional",
        )
        resp = client.get(
            f"{BASE}/",
            headers=juridico_headers,
            params={
                "tematica_principal": "regulacion_normativa",
                "ambito_aplicacion": "nacional",
            },
        )
        assert resp.status_code == 200
        assert any(i["id"] == creado["id"] for i in resp.json()["items"])

    def test_filtro_por_palabra_clave(self, client, juridico_headers):
        marca = uuid.uuid4().hex[:10]
        creado = _crear(client, juridico_headers, palabras_clave=[marca])
        resp = client.get(f"{BASE}/", headers=juridico_headers, params={"q": marca})
        assert resp.status_code == 200
        assert [i["id"] for i in resp.json()["items"]] == [creado["id"]]

    def test_filtro_por_vigencia(self, client, juridico_headers):
        vigente = _crear(
            client,
            juridico_headers,
            fecha_inicio_vigencia="2020-01-01",
            fecha_expiracion="2099-12-31",
        )
        vencido = _crear(
            client,
            juridico_headers,
            fecha_inicio_vigencia="2010-01-01",
            fecha_expiracion="2011-01-01",
        )
        ids_vigentes = [
            i["id"]
            for i in client.get(
                f"{BASE}/", headers=juridico_headers, params={"vigente": True, "limit": 200}
            ).json()["items"]
        ]
        assert vigente["id"] in ids_vigentes
        assert vencido["id"] not in ids_vigentes

        ids_no_vigentes = [
            i["id"]
            for i in client.get(
                f"{BASE}/", headers=juridico_headers, params={"vigente": False, "limit": 200}
            ).json()["items"]
        ]
        assert vencido["id"] in ids_no_vigentes


# ---------------------------------------------------------------------------
# Informes
# ---------------------------------------------------------------------------


class TestInstrumentoStats:
    def test_stats_requires_auth(self, client):
        assert client.get(f"{BASE}/admin/stats/resumen").status_code == 401

    def test_stats_forbidden_for_regular_user(self, client, user_headers):
        resp = client.get(f"{BASE}/admin/stats/resumen", headers=user_headers)
        assert resp.status_code == 403

    def test_stats_resumen(self, client, juridico_headers):
        _crear(
            client,
            juridico_headers,
            tipo_documento="convenio_aporte",
            fecha_emision="2025-02-01",
            fecha_inicio_vigencia="2025-02-01",
            fecha_expiracion="2099-01-01",
            areas_vinculadas=["juridico"],
        )
        resp = client.get(f"{BASE}/admin/stats/resumen", headers=juridico_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert {"total", "por_anio", "por_area", "convenios_vigentes"}.issubset(
            body.keys()
        )
        assert body["total"] >= 1
        assert body["por_anio"].get("2025", 0) >= 1
        assert body["por_area"].get("juridico", 0) >= 1
        assert body["convenios_vigentes"] >= 1


# ---------------------------------------------------------------------------
# Auditoría (el "historial de modificaciones" de la sección 7)
# ---------------------------------------------------------------------------


def test_alta_queda_auditada(client, juridico_headers, db_session, instrumento):
    from src.models.audit_model import AuditLog

    registro = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.resource_type == "InstrumentoJuridico",
            AuditLog.resource_id == str(instrumento["id"]),
        )
        .first()
    )
    assert registro is not None
    assert registro.action == "CREATE"


# ---------------------------------------------------------------------------
# Borrador: lo que habilita el autoguardado del formulario
# ---------------------------------------------------------------------------


class TestInstrumentoBorrador:
    """
    El formulario del area autoguarda desde el primer campo, igual que los del
    Padron. Eso exige poder crear una fila incompleta — y exigir los campos
    obligatorios recien al darla por cargada.
    """

    def test_se_puede_crear_un_borrador_casi_vacio(self, client, admin_headers):
        # Lo que manda el autoguardado apenas se escribe el titulo.
        resp = client.post(
            BASE + "/", headers=admin_headers, json={"borrador": True, "titulo": "Sin terminar"}
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["borrador"] is True
        assert resp.json()["tipo_documento"] is None

    def test_no_se_puede_crear_uno_no_borrador_incompleto(self, client, admin_headers):
        resp = client.post(BASE + "/", headers=admin_headers, json={"titulo": "Sin terminar"})
        assert resp.status_code == 422, resp.text
        # El mensaje tiene que decir QUE falta, no solo que algo falta.
        detalle = resp.json()["detail"]
        assert "tipo de documento" in detalle and "resumen" in detalle

    def test_un_put_puede_completar_y_enviar_en_una_sola_llamada(
        self, client, admin_headers
    ):
        creado = client.post(
            BASE + "/", headers=admin_headers, json={"borrador": True, "titulo": "A medias"}
        ).json()

        # Se valida contra el estado RESULTANTE: el mismo PUT completa lo que
        # falta y saca el borrador.
        resp = client.put(
            f"{BASE}/{creado['id']}",
            headers=admin_headers,
            json={
                "borrador": False,
                "tipo_documento": "resolucion",
                "resumen": "Un resumen.",
                "archivo_pdf_path": "u1/instrumento_abc.pdf",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["borrador"] is False

    def test_no_se_puede_sacar_el_borrador_sin_completar(self, client, admin_headers):
        creado = client.post(
            BASE + "/", headers=admin_headers, json={"borrador": True, "titulo": "A medias"}
        ).json()
        resp = client.put(
            f"{BASE}/{creado['id']}", headers=admin_headers, json={"borrador": False}
        )
        assert resp.status_code == 422, resp.text

    def test_un_borrador_se_puede_seguir_guardando_incompleto(
        self, client, admin_headers
    ):
        creado = client.post(
            BASE + "/", headers=admin_headers, json={"borrador": True, "titulo": "Paso 1"}
        ).json()
        resp = client.put(
            f"{BASE}/{creado['id']}",
            headers=admin_headers,
            json={"borrador": True, "titulo": "Paso 2"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["titulo"] == "Paso 2"


# ---------------------------------------------------------------------------
# Descarga de adjuntos
# ---------------------------------------------------------------------------
class TestInstrumentoAdjuntos:
    """
    El PDF lo sube un gestor y lo abre otro: se sirve desde el directorio de
    quien lo subio, no del que lo pide. La ruta la escribe el cliente, asi que
    solo se sirven archivos con el formato que genera upload_document para el
    tipo correspondiente.
    """

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

    def test_descarga_el_pdf_subido_por_otro_usuario(
        self, client, juridico_headers, uploads
    ):
        ruta = self._archivo(uploads, "otro-gestor", "instrumento_juridico_abc.pdf")
        creado = _crear(client, juridico_headers, archivo_pdf_path=ruta)
        resp = client.get(f"{BASE}/{creado['id']}/pdf", headers=juridico_headers)
        assert resp.status_code == 200, resp.text
        assert resp.content.startswith(b"%PDF")

    def test_no_sirve_un_archivo_de_otro_tipo(self, client, juridico_headers, uploads):
        # Un DNI ajeno no se puede sacar apuntando el campo a su ruta.
        ruta = self._archivo(uploads, "victima", "dni_abc.pdf")
        creado = _crear(client, juridico_headers, archivo_pdf_path=ruta)
        resp = client.get(f"{BASE}/{creado['id']}/pdf", headers=juridico_headers)
        assert resp.status_code == 404

    def test_no_sirve_rutas_que_salen_del_directorio(
        self, client, juridico_headers, uploads
    ):
        creado = _crear(
            client, juridico_headers,
            archivo_pdf_path="../instrumento_juridico_abc.pdf",
        )
        resp = client.get(f"{BASE}/{creado['id']}/pdf", headers=juridico_headers)
        assert resp.status_code in (403, 404)

    def test_descarga_el_pdf_del_acta(self, client, juridico_headers, uploads):
        ruta = self._archivo(uploads, "otro-gestor", "acta_consejo_directivo_abc.pdf")
        creado = _crear(
            client, juridico_headers,
            tipo_documento="acta_consejo_directivo",
            acta={"acta_pdf_path": ruta},
        )
        resp = client.get(f"{BASE}/{creado['id']}/acta-pdf", headers=juridico_headers)
        assert resp.status_code == 200, resp.text

    def test_adjunto_desconocido_es_404(self, client, juridico_headers, instrumento):
        resp = client.get(f"{BASE}/{instrumento['id']}/otra-cosa", headers=juridico_headers)
        assert resp.status_code == 404

    def test_sin_permiso_es_403(self, client, user_headers, instrumento):
        resp = client.get(f"{BASE}/{instrumento['id']}/pdf", headers=user_headers)
        assert resp.status_code == 403
