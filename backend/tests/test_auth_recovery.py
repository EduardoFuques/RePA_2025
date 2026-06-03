"""
Tests de recuperación de contraseña, tokens y gestión de la propia cuenta.

Complementa a test_auth.py (registro/login/perfil) cubriendo:
- Flujo completo de recuperación de contraseña (generar token → resetear → login).
- No filtración de existencia de email (respuesta genérica).
- Validación de contraseña en recovery y en update.
- Tokens inválidos / de tipo incorrecto en /recovery/{token}.
- El login emite refresh_token.
- Baja de cuenta con confirmación de contraseña.
"""
import uuid

import pytest


@pytest.fixture
def cuenta(create_user):
    """Crea un usuario activo fresco y devuelve (user, headers, password)."""
    email = f"recover_{uuid.uuid4().hex[:8]}@example.com"
    password = "Passw0rd!"
    user, headers = create_user(email, password=password)
    return user, headers, password


def _token_recovery_de(db_session, user_id):
    from src.models.user_models import TokenRecovery

    db_session.rollback()  # snapshot fresco (lee lo ya commiteado por la API)
    return (
        db_session.query(TokenRecovery)
        .filter(
            TokenRecovery.user_id == user_id,
            TokenRecovery.is_active.is_(True),
        )
        .order_by(TokenRecovery.id.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------


class TestRecoveryPassword:
    def test_flujo_completo(self, client, cuenta, db_session):
        user, _headers, old_password = cuenta
        new_password = "NuevaClave1"

        # 1) Solicitar recuperación
        resp = client.put(
            "/users/recovery_passwd",
            json={"email": user.email, "password": new_password},
        )
        assert resp.status_code == 200

        # 2) Recuperar el token generado (en producción llegaría por email)
        record = _token_recovery_de(db_session, user.id)
        assert record is not None

        # 3) Aplicar el reset con el token
        reset = client.post(f"/users/recovery/{record.token_payload}")
        assert reset.status_code == 200, reset.text

        # 4) La contraseña nueva funciona y la vieja ya no
        ok = client.post(
            "/users/token",
            data={"username": user.email, "password": new_password},
        )
        assert ok.status_code == 200
        fail = client.post(
            "/users/token",
            data={"username": user.email, "password": old_password},
        )
        assert fail.status_code == 400

    def test_email_inexistente_respuesta_generica(self, client):
        # No debe revelar si el email existe: responde 200 genérico
        resp = client.put(
            "/users/recovery_passwd",
            json={
                "email": f"nadie_{uuid.uuid4().hex[:8]}@example.com",
                "password": "NuevaClave1",
            },
        )
        assert resp.status_code == 200

    def test_password_debil_es_400(self, client, cuenta):
        user, _headers, _password = cuenta
        resp = client.put(
            "/users/recovery_passwd",
            json={"email": user.email, "password": "debil"},
        )
        assert resp.status_code == 400

    def test_token_invalido_es_401(self, client):
        resp = client.post("/users/recovery/token-que-no-es-jwt")
        assert resp.status_code == 401

    def test_token_tipo_incorrecto_es_400(self, client, cuenta):
        # Un access_token válido no sirve como token de recover (type != 'recover')
        _user, headers, _password = cuenta
        access_token = headers["Authorization"].split(" ", 1)[1]
        resp = client.post(f"/users/recovery/{access_token}")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Tokens de login
# ---------------------------------------------------------------------------


class TestLoginTokens:
    def test_login_emite_refresh_token(self, client, cuenta):
        user, _headers, password = cuenta
        resp = client.post(
            "/users/token",
            data={"username": user.email, "password": password},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# Gestión de la propia cuenta (/users/me)
# ---------------------------------------------------------------------------


class TestUpdateMe:
    def test_update_password_debil_es_400(self, client, cuenta):
        _user, headers, _password = cuenta
        resp = client.put("/users/me", headers=headers, json={"password": "debil"})
        assert resp.status_code == 400

    def test_update_email_ok(self, client, cuenta):
        _user, headers, _password = cuenta
        nuevo = f"updated_{uuid.uuid4().hex[:8]}@example.com"
        resp = client.put("/users/me", headers=headers, json={"email": nuevo})
        assert resp.status_code == 200
        assert resp.json()["email"] == nuevo

    def test_update_requires_auth(self, client):
        resp = client.put("/users/me", json={"email": "x@example.com"})
        assert resp.status_code == 401


class TestDeleteMe:
    def test_password_incorrecta_es_400(self, client, cuenta):
        _user, headers, _password = cuenta
        resp = client.request(
            "DELETE", "/users/me", headers=headers, json={"password": "incorrecta"}
        )
        assert resp.status_code == 400

    def test_baja_desactiva_y_bloquea_login(self, client, cuenta):
        user, headers, password = cuenta
        # Baja con confirmación correcta
        resp = client.request(
            "DELETE", "/users/me", headers=headers, json={"password": password}
        )
        assert resp.status_code == 200

        # Cuenta desactivada → login devuelve 403 (no verificada/activa)
        login = client.post(
            "/users/token",
            data={"username": user.email, "password": password},
        )
        assert login.status_code == 403
