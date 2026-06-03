"""
Casos de borde transversales (Fase 7.2):

- Unicidad "un registro por usuario" en formularios (PF/PJ/AS) → 400.
- Expiración de access token → 401.
- Rate limiting en login → 429 (el limiter se habilita puntualmente porque
  en el entorno de tests está deshabilitado por defecto).

Los imports de `src.*` se hacen DENTRO de fixtures/tests para no fijar
DATABASE_URL en tiempo de colección.
"""
import uuid

import pytest


@pytest.fixture
def usuario(create_user):
    """Usuario regular fresco (headers)."""
    _user, headers = create_user(f"edge_{uuid.uuid4().hex[:8]}@example.com")
    return headers


# ---------------------------------------------------------------------------
# Unicidad: un único registro por usuario
# ---------------------------------------------------------------------------


class TestUnRegistroPorUsuario:
    @pytest.mark.parametrize(
        "endpoint",
        ["/persona-fisica/", "/persona-juridica/", "/asociacion/"],
    )
    def test_segundo_registro_es_400(self, client, usuario, endpoint):
        # Primer registro (borrador vacío, sin dni/cuit para no chocar con
        # restricciones únicas entre usuarios)
        primero = client.post(endpoint, headers=usuario, json={})
        assert primero.status_code == 201, primero.text

        # Segundo registro del mismo usuario → 400 (ya tiene uno)
        segundo = client.post(endpoint, headers=usuario, json={})
        assert segundo.status_code == 400

    def test_dni_duplicado_entre_usuarios_es_409(self, client, create_user):
        # Dos usuarios distintos no pueden compartir el mismo DNI (constraint
        # UNIQUE de DB). Debe responder 409, no 500.
        dni = f"DNI{uuid.uuid4().hex[:8]}"
        _u1, h1 = create_user(f"dni_a_{uuid.uuid4().hex[:8]}@example.com")
        _u2, h2 = create_user(f"dni_b_{uuid.uuid4().hex[:8]}@example.com")

        r1 = client.post("/persona-fisica/", headers=h1, json={"dni": dni})
        assert r1.status_code == 201, r1.text

        r2 = client.post("/persona-fisica/", headers=h2, json={"dni": dni})
        assert r2.status_code == 409


# ---------------------------------------------------------------------------
# Expiración / validez de tokens
# ---------------------------------------------------------------------------


class TestTokenExpiration:
    def test_access_token_expirado_es_401(self, client):
        from src.token_utils import create_access_token

        expirado = create_access_token(
            data={"sub": "fake-id", "email": "x@example.com", "roles": []},
            expires_delta=-1,  # vencido hace 1 minuto
        )
        resp = client.get(
            "/users/me", headers={"Authorization": f"Bearer {expirado}"}
        )
        assert resp.status_code == 401
        assert "expirado" in resp.json()["detail"].lower()

    def test_access_token_firma_invalida_es_401(self, client):
        # Token con firma incorrecta (otra clave)
        import jwt

        falso = jwt.encode(
            {"sub": "fake-id", "type": "access"}, "clave-incorrecta", algorithm="HS256"
        )
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {falso}"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    def test_login_excede_limite_devuelve_429(self, client, monkeypatch):
        from src.rate_limiter import limiter

        # Habilitar el limiter solo para este test (se restaura al finalizar)
        monkeypatch.setattr(limiter, "enabled", True)
        if hasattr(limiter, "reset"):
            limiter.reset()

        # Límite del endpoint: 5/minuto. Incluso credenciales inválidas (400)
        # consumen el cupo porque el límite se evalúa antes del handler.
        statuses = []
        for _ in range(6):
            r = client.post(
                "/users/token",
                data={"username": "inexistente@example.com", "password": "x"},
            )
            statuses.append(r.status_code)

        assert 429 in statuses, statuses
        # El 429 debe aparecer recién tras agotar el cupo (no en el primer intento)
        assert statuses[0] != 429
