# tests/test_auth.py
"""Tests para autenticación y usuarios"""
import pytest


class TestUserRegistration:
    """Tests para registro de usuarios"""
    
    def test_register_user_success(self, client):
        """Test: Registro exitoso de usuario"""
        response = client.post(
            "/users/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "email" in data or "id" in data
    
    def test_register_user_duplicate_email(self, client):
        """Test: No permite registrar email duplicado"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        }
        # Primer registro
        client.post("/users/register", json=user_data)
        # Segundo registro con mismo email
        response = client.post("/users/register", json=user_data)
        assert response.status_code == 400
    
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
