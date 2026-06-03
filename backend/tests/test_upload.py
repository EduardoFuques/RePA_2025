"""
Tests del módulo de Upload de archivos.

Cubre validaciones de seguridad y contrato:
- Autenticación requerida (401).
- Validación de content-type, extensión y magic bytes (400).
- Aislamiento por usuario / protección path traversal (403).
- Happy path de subida + descarga + borrado.

`UPLOAD_BASE_DIR` se redirige a un directorio temporal por test para no tocar
el filesystem real (`/app/uploads`).
"""
import pytest

# IMPORTANTE: no importar src.* a nivel de módulo. Hacerlo en tiempo de
# colección fijaría DATABASE_URL desde .env antes de que el contenedor de
# tests configure su URL. Los imports de src van dentro de fixtures/tests.

# Bytes mínimos válidos por tipo (coinciden con los magic bytes del backend)
PDF_BYTES = b"%PDF-1.4\n%EOF\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 16


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Redirige UPLOAD_BASE_DIR a un tmp aislado por test."""
    import src.routes.upload_routes as upload_routes

    monkeypatch.setattr(upload_routes, "UPLOAD_BASE_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def uploader(create_user):
    """Usuario regular fresco autenticado para subir archivos."""
    import uuid

    _user, headers = create_user(f"upload_{uuid.uuid4().hex[:8]}@example.com")
    return headers


# ---------------------------------------------------------------------------
# POST /upload/dni
# ---------------------------------------------------------------------------


class TestUploadDni:
    def test_requires_auth(self, client):
        resp = client.post(
            "/upload/dni", files={"file": ("dni.pdf", PDF_BYTES, "application/pdf")}
        )
        assert resp.status_code == 401

    def test_rejects_non_pdf_content_type(self, client, uploader):
        resp = client.post(
            "/upload/dni",
            headers=uploader,
            files={"file": ("dni.txt", b"hola", "text/plain")},
        )
        assert resp.status_code == 400

    def test_rejects_bad_magic_bytes(self, client, uploader):
        # content-type correcto pero contenido no es un PDF real
        resp = client.post(
            "/upload/dni",
            headers=uploader,
            files={"file": ("dni.pdf", b"NO-ES-PDF", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_happy_path_upload_and_delete(self, client, uploader):
        up = client.post(
            "/upload/dni",
            headers=uploader,
            files={"file": ("dni.pdf", PDF_BYTES, "application/pdf")},
        )
        assert up.status_code == 200, up.text
        body = up.json()
        assert "path" in body and "filename" in body

        # Borrar el archivo recién subido
        delete = client.delete(
            f"/upload/dni/{body['filename']}", headers=uploader
        )
        assert delete.status_code == 200

        # Volver a borrar → 404
        delete2 = client.delete(
            f"/upload/dni/{body['filename']}", headers=uploader
        )
        assert delete2.status_code == 404


# ---------------------------------------------------------------------------
# POST /upload/document/{doc_type}
# ---------------------------------------------------------------------------


class TestUploadDocument:
    def test_requires_auth(self, client):
        resp = client.post(
            "/upload/document/estatuto",
            files={"file": ("e.pdf", PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 401

    def test_invalid_doc_type(self, client, uploader):
        resp = client.post(
            "/upload/document/tipo_inexistente",
            headers=uploader,
            files={"file": ("e.pdf", PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 400

    def test_invalid_extension(self, client, uploader):
        # estatuto no admite .txt
        resp = client.post(
            "/upload/document/estatuto",
            headers=uploader,
            files={"file": ("e.txt", b"hola", "text/plain")},
        )
        assert resp.status_code == 400

    def test_bad_magic_bytes(self, client, uploader):
        resp = client.post(
            "/upload/document/estatuto",
            headers=uploader,
            files={"file": ("e.pdf", b"NO-PDF", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_happy_path_pdf(self, client, uploader):
        resp = client.post(
            "/upload/document/estatuto",
            headers=uploader,
            files={"file": ("e.pdf", PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["filename"].startswith("estatuto_")

    def test_happy_path_png(self, client, uploader):
        resp = client.post(
            "/upload/document/estatuto",
            headers=uploader,
            files={"file": ("e.png", PNG_BYTES, "image/png")},
        )
        assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# GET /upload/document/{filepath} — aislamiento por usuario
# ---------------------------------------------------------------------------


class TestGetDocument:
    def test_other_user_path_forbidden(self, client, uploader):
        # Intentar acceder a la carpeta de otro usuario → 403
        resp = client.get(
            "/upload/document/otro-usuario-id/archivo.pdf", headers=uploader
        )
        assert resp.status_code == 403

    def test_own_missing_file_is_404(self, client, uploader):
        resp = client.get("/upload/document/inexistente.pdf", headers=uploader)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /files/view y /files/download
# ---------------------------------------------------------------------------


class TestFilesAlias:
    def test_view_requires_auth(self, client):
        resp = client.get("/files/view/algo.pdf")
        assert resp.status_code == 401

    def test_view_missing_file_is_404(self, client, uploader):
        resp = client.get("/files/view/inexistente.pdf", headers=uploader)
        assert resp.status_code == 404

    def test_download_missing_file_is_404(self, client, uploader):
        resp = client.get("/files/download/inexistente.pdf", headers=uploader)
        assert resp.status_code == 404
