# tests/test_auth.py
"""Tests para autenticación y usuarios"""
from uuid import uuid4

import pytest


class TestUserRegistration:
    """Tests para registro de usuarios"""
    
    def test_register_user_success(self, client):
        """Test: Registro exitoso de usuario (respuesta mínima anti-enumeración)"""
        response = client.post(
            "/users/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "message" in data
        # En entorno de test (no producción) se expone el token de verificación
        assert "verification_token" in data

    def test_register_user_duplicate_email(self, client):
        """Test: email duplicado devuelve la misma respuesta genérica (201),
        sin revelar que la cuenta existe, y no crea un segundo usuario."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        }
        # Primer registro
        first = client.post("/users/register", json=user_data)
        assert first.status_code == 201
        # Segundo registro con mismo email: mismo status y mismo mensaje
        response = client.post("/users/register", json=user_data)
        assert response.status_code == 201
        assert response.json()["message"] == first.json()["message"]
        # No emite token de verificación para la cuenta ya existente
        assert "verification_token" not in response.json()
    
    def test_register_user_invalid_email(self, client):
        """Test: Rechaza email inválido"""
        response = client.post(
            "/users/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    """Tests para login de usuarios"""
    
    def test_login_success(self, client, test_user_data, db_session):
        """Test: Login exitoso"""
        from src.models.user_models import User

        # Registrar usuario
        client.post("/users/register", json=test_user_data)

        # Activar el usuario (bypass verificación de email) para que el login
        # sea determinista sin depender del orden de ejecución de otros tests.
        db_session.commit()
        user = (
            db_session.query(User)
            .filter(User.email == test_user_data["email"])
            .first()
        )
        if user and not user.is_active:
            user.is_active = True
            db_session.commit()
        
        # Login
        response = client.post(
            "/users/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user_data):
        """Test: Login con contraseña incorrecta devuelve error 400"""
        # Registrar usuario
        client.post("/users/register", json=test_user_data)
        
        # Login con contraseña incorrecta - debe fallar con 400
        response = client.post(
            "/users/token",
            data={
                "username": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )
        # Backend devuelve 400 para credenciales incorrectas
        assert response.status_code == 400
        assert "incorrecto" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test: Login con usuario inexistente devuelve error 400"""
        response = client.post(
            "/users/token",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        # Backend devuelve 400 para usuario no encontrado
        assert response.status_code == 400


class TestTokenRefresh:
    """Tests para POST /users/refresh (renovación de sesión sin credenciales)"""

    def _login(self, client, test_user_data, db_session):
        from src.models.user_models import User

        client.post("/users/register", json=test_user_data)
        db_session.commit()
        user = (
            db_session.query(User)
            .filter(User.email == test_user_data["email"])
            .first()
        )
        if user and not user.is_active:
            user.is_active = True
            db_session.commit()

        return client.post(
            "/users/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        ).json()

    def test_refresh_con_refresh_token_valido_devuelve_access_token_nuevo(
        self, client, test_user_data, db_session
    ):
        tokens = self._login(client, test_user_data, db_session)
        assert "refresh_token" in tokens

        response = client.post(
            "/users/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # El access_token nuevo autentica endpoints protegidos.
        me = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me.status_code == 200

    def test_refresh_con_access_token_es_rechazado(
        self, client, test_user_data, db_session
    ):
        """Un access_token (type=access) no debe servir como refresh_token."""
        tokens = self._login(client, test_user_data, db_session)

        response = client.post(
            "/users/refresh", json={"refresh_token": tokens["access_token"]}
        )
        assert response.status_code == 401

    def test_refresh_con_token_invalido_es_401(self, client):
        response = client.post(
            "/users/refresh", json={"refresh_token": "no-es-un-jwt"}
        )
        assert response.status_code == 401

    def test_refresh_de_usuario_inactivo_es_401(
        self, client, test_user_data, db_session
    ):
        from src.models.user_models import User

        tokens = self._login(client, test_user_data, db_session)
        user = (
            db_session.query(User)
            .filter(User.email == test_user_data["email"])
            .first()
        )
        user.is_active = False
        db_session.commit()

        response = client.post(
            "/users/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 401


class TestResendVerification:
    """Tests para POST /users/resend-verification

    Usa emails únicos por test (no el `test_user_data` compartido): la DB de
    test vive en un único testcontainer para toda la corrida, así que un
    email fijo reusado por otras clases (que sí activan la cuenta) haría que
    estos tests hereden un usuario ya activo sin darse cuenta.
    """

    def _unique_user(self):
        return {
            "email": f"resend-{uuid4()}@example.com",
            "password": "TestPassword123!",
        }

    def test_resend_for_inactive_user_creates_new_token_and_invalidates_old(
        self, client
    ):
        user_data = self._unique_user()
        register = client.post("/users/register", json=user_data)
        old_token = register.json()["verification_token"]

        response = client.post(
            "/users/resend-verification", json={"email": user_data["email"]}
        )
        assert response.status_code == 200
        new_token = response.json()["verification_token"]
        assert new_token != old_token

        # El token viejo ya no sirve.
        old_confirm = client.post(f"/users/confirm/{old_token}")
        assert old_confirm.status_code == 404

        # El nuevo token confirma la cuenta correctamente.
        new_confirm = client.post(f"/users/confirm/{new_token}")
        assert new_confirm.status_code == 201

    def test_resend_for_active_user_returns_generic_message_and_does_nothing(
        self, client, db_session
    ):
        from src.models.user_models import User

        user_data = self._unique_user()
        client.post("/users/register", json=user_data)
        db_session.commit()
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        user.is_active = True
        db_session.commit()

        response = client.post(
            "/users/resend-verification", json={"email": user_data["email"]}
        )
        assert response.status_code == 200
        assert "verification_token" not in response.json()

    def test_resend_for_nonexistent_email_returns_same_generic_message(self, client):
        active_check = client.post(
            "/users/resend-verification",
            json={"email": f"no-existe-{uuid4()}@example.com"},
        )
        assert active_check.status_code == 200
        assert "verification_token" not in active_check.json()
        # Mismo mensaje genérico independientemente del caso (anti-enumeración).
        assert (
            active_check.json()["detail"]
            == "Si el email está registrado y pendiente de verificación, recibirás un nuevo correo de confirmación."
        )

    def test_resend_invalidates_pending_recovery_token_too(self, client, db_session):
        from src.models.user_models import TokenRecovery, User

        user_data = self._unique_user()
        client.post("/users/register", json=user_data)
        db_session.commit()
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        # Simula un token de recuperación (recover) también activo para el
        # mismo usuario (aunque no debería poder pedirse estando inactivo,
        # probamos que el reenvío igual lo invalida por higiene).
        recover_record = TokenRecovery(
            user_id=user.id,
            token_payload="fake-recover-token-payload",
            is_active=True,
        )
        db_session.add(recover_record)
        db_session.commit()

        client.post(
            "/users/resend-verification", json={"email": user_data["email"]}
        )

        db_session.refresh(recover_record)
        assert recover_record.is_active is False


class TestUserProfile:
    """Tests para perfil de usuario"""
    
    def test_get_current_user(self, client, auth_headers):
        """Test: Obtener datos del usuario actual"""
        if not auth_headers:
            pytest.skip("No se pudo autenticar")
        
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test: Acceso sin autenticación"""
        response = client.get("/users/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Test: Acceso con token inválido"""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
