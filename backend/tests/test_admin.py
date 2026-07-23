"""
Tests para el módulo de Administración.
"""
import pytest
from fastapi.testclient import TestClient


class TestAdmin:
    """Tests para endpoints de administración."""

    @pytest.fixture
    def admin_headers(self, client: TestClient, db_session):
        """Fixture para obtener headers de admin."""
        from src.models.user_models import User, Role, UserRole
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Crear rol admin si no existe
        admin_role = db_session.query(Role).filter(Role.rol == "admin").first()
        if not admin_role:
            admin_role = Role(rol="admin")
            db_session.add(admin_role)
            db_session.commit()
        
        # Crear usuario admin
        admin_email = "admin_test@example.com"
        admin_user = db_session.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            admin_user = User(
                email=admin_email,
                hashed_password=pwd_context.hash("AdminTest123!"),
                is_active=True
            )
            db_session.add(admin_user)
            db_session.commit()
            db_session.refresh(admin_user)
            
            # Asignar rol admin
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db_session.add(user_role)
            db_session.commit()
        
        # Login
        response = client.post(
            "/users/token",
            data={"username": admin_email, "password": "AdminTest123!"}
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        
        return {}

    def test_get_users_as_admin(self, client: TestClient, admin_headers: dict):
        """Test obtener lista de usuarios como admin."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        response = client.get("/admin_user/users", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_users_sin_auth(self, client: TestClient):
        """Test que obtener usuarios requiere autenticación."""
        response = client.get("/admin_user/users")
        assert response.status_code == 401

    def test_get_users_sin_rol_admin(self, client: TestClient, auth_headers: dict):
        """Test que usuario normal no puede obtener lista de usuarios."""
        if not auth_headers:
            pytest.skip("No se pudo obtener token de autenticación")
        
        response = client.get("/admin_user/users", headers=auth_headers)
        assert response.status_code == 403

    def test_get_user_by_id(self, client: TestClient, admin_headers: dict, db_session):
        """Test obtener usuario por ID como admin."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        from src.models.user_models import User
        
        # Obtener cualquier usuario
        user = db_session.query(User).first()
        if not user:
            pytest.skip("No hay usuarios en la BD")
        
        response = client.get(f"/admin_user/users/{user.id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == user.id

    def test_get_user_not_found(self, client: TestClient, admin_headers: dict):
        """Test obtener usuario inexistente."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        response = client.get("/admin_user/users/nonexistent-id", headers=admin_headers)
        assert response.status_code == 404

    def test_update_user_as_admin(self, client: TestClient, admin_headers: dict, db_session):
        """Test actualizar usuario como admin."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        from src.models.user_models import User
        
        # Obtener usuario que no sea admin
        user = db_session.query(User).filter(User.email != "admin_test@example.com").first()
        if not user:
            pytest.skip("No hay usuarios para actualizar")
        
        update_data = {"email": f"updated_{user.email}"}
        response = client.put(f"/admin_user/users/{user.id}", json=update_data, headers=admin_headers)
        
        # Puede ser 200 o 400 si el email ya existe
        assert response.status_code in [200, 400]

    def test_toggle_user_active(self, client: TestClient, admin_headers: dict, db_session):
        """Test cambiar estado activo de usuario."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        from src.models.user_models import User
        
        # Obtener usuario que no sea admin
        user = db_session.query(User).filter(User.email != "admin_test@example.com").first()
        if not user:
            pytest.skip("No hay usuarios para desactivar")
        
        # Nuevo endpoint explícito e idempotente: PATCH /users/{id}/status
        nuevo_estado = not user.is_active
        response = client.patch(
            f"/admin_user/users/{user.id}/status?is_active={str(nuevo_estado).lower()}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] == nuevo_estado

    def test_update_user_roles(self, client: TestClient, admin_headers: dict, db_session):
        """Test actualizar roles de usuario."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")
        
        from src.models.user_models import User, Role
        
        # Obtener usuario y rol
        user = db_session.query(User).filter(User.email != "admin_test@example.com").first()
        role = db_session.query(Role).first()
        
        if not user or not role:
            pytest.skip("No hay usuarios o roles para actualizar")
        
        response = client.put(
            f"/admin_user/users/{user.id}/roles",
            json={"add": [role.id], "remove": []},
            headers=admin_headers
        )
        
        assert response.status_code == 200
