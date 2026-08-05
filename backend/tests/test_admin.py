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
        """Test obtener lista de usuarios como admin.

        El endpoint devuelve `{items, total, offset, limit}` (antes: una lista
        sin paginar con TODOS los usuarios).
        """
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")

        response = client.get("/admin_user/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        assert data["total"] >= len(data["items"])
        assert data["offset"] == 0

    def test_get_users_paginacion(self, client: TestClient, admin_headers: dict):
        """La paginación recorta `items` sin alterar `total`."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")

        completo = client.get("/admin_user/users", headers=admin_headers).json()
        if completo["total"] < 2:
            pytest.skip("Hacen falta al menos 2 usuarios para probar paginación")

        pagina = client.get(
            "/admin_user/users?limit=1&offset=0", headers=admin_headers
        ).json()
        assert len(pagina["items"]) == 1
        assert pagina["total"] == completo["total"]

        segunda = client.get(
            "/admin_user/users?limit=1&offset=1", headers=admin_headers
        ).json()
        assert segunda["items"][0]["id"] != pagina["items"][0]["id"]

    def test_get_users_filtros(self, client: TestClient, admin_headers: dict):
        """Búsqueda por email, filtro por rol y por estado."""
        if not admin_headers:
            pytest.skip("No se pudo obtener token de admin")

        todos = client.get("/admin_user/users?limit=200", headers=admin_headers).json()
        objetivo = todos["items"][0]

        # Búsqueda por email: el usuario buscado tiene que aparecer.
        encontrado = client.get(
            f"/admin_user/users?search={objetivo['email']}", headers=admin_headers
        ).json()
        assert objetivo["id"] in [u["id"] for u in encontrado["items"]]

        # Filtro por estado: nada activo aparece bajo is_active=false.
        inactivos = client.get(
            "/admin_user/users?is_active=false&limit=200", headers=admin_headers
        ).json()
        assert all(u["is_active"] is False for u in inactivos["items"])

        # Filtro por rol: todos los devueltos tienen ese rol.
        admins = client.get(
            "/admin_user/users?role=admin&limit=200", headers=admin_headers
        ).json()
        assert all(
            any(r["rol"] == "admin" for r in u["roles"]) for u in admins["items"]
        )

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
        
        # Obtener usuario y rol. Excluye el rol "admin" a propósito: designar
        # admin exige que el usuario ya tenga una Persona Física en el Padrón
        # (ver admin_routes.py update_user_roles) — esa regla ya tiene su
        # propia cobertura en TestDesignarAdminRequierePersonaFisica más
        # abajo. Este test solo verifica el camino feliz genérico de
        # actualizar roles, así que agarrar "admin" acá era un choque con
        # esa regla, no con lo que el test dice probar.
        user = db_session.query(User).filter(User.email != "admin_test@example.com").first()
        role = db_session.query(Role).filter(Role.rol != "admin").first()

        if not user or not role:
            pytest.skip("No hay usuarios o roles para actualizar")
        
        response = client.put(
            f"/admin_user/users/{user.id}/roles",
            json={"add": [role.id], "remove": []},
            headers=admin_headers
        )

        assert response.status_code == 200


class TestDesignarAdminRequierePersonaFisica:
    """Para ser designado administrador, el usuario ya tiene que estar en la
    plataforma: tener un registro de Persona Física en el Padrón."""

    def _admin_role_id(self, db_session):
        from src.models.user_models import Role

        db_session.rollback()
        return db_session.query(Role).filter(Role.rol == "admin").first().id

    def test_sin_persona_fisica_es_400(self, client, create_user, admin_headers, db_session):
        candidato, _ = create_user(
            f"sinpf_{__import__('uuid').uuid4().hex[:8]}@example.com", roles=["user"]
        )
        admin_role_id = self._admin_role_id(db_session)

        resp = client.put(
            f"/admin_user/users/{candidato.id}/roles",
            headers=admin_headers,
            json={"add": [admin_role_id], "remove": []},
        )
        assert resp.status_code == 400
        assert "Persona Física" in resp.json()["detail"]

    def test_con_persona_fisica_permite_otorgar(self, client, create_user, admin_headers, db_session):
        from src.models.persona_fisica_model import PersonaFisica

        candidato, _ = create_user(
            f"conpf_{__import__('uuid').uuid4().hex[:8]}@example.com", roles=["user"]
        )
        db_session.add(PersonaFisica(user_id=candidato.id))
        db_session.commit()
        admin_role_id = self._admin_role_id(db_session)

        resp = client.put(
            f"/admin_user/users/{candidato.id}/roles",
            headers=admin_headers,
            json={"add": [admin_role_id], "remove": []},
        )
        assert resp.status_code == 200
        assert any(r["rol"] == "admin" for r in resp.json()["roles"])

    def test_listado_indica_quien_tiene_pf(self, client, create_user, admin_headers, db_session):
        from src.models.persona_fisica_model import PersonaFisica

        con_pf, _ = create_user(
            f"listapf_{__import__('uuid').uuid4().hex[:8]}@example.com", roles=["user"]
        )
        db_session.add(PersonaFisica(user_id=con_pf.id))
        db_session.commit()
        sin_pf, _ = create_user(
            f"listasinpf_{__import__('uuid').uuid4().hex[:8]}@example.com", roles=["user"]
        )

        data = client.get(
            f"/admin_user/users?search={con_pf.email}", headers=admin_headers
        ).json()
        assert data["items"][0]["tiene_persona_fisica"] is True

        data = client.get(
            f"/admin_user/users?search={sin_pf.email}", headers=admin_headers
        ).json()
        assert data["items"][0]["tiene_persona_fisica"] is False

    def test_no_aplica_si_ya_era_admin(self, client, create_user, admin_headers, db_session):
        """Un patch que no agrega el rol admin de nuevo (ya lo tenía) no debe
        exigir Persona Física — ej. tocar solo otro rol en el mismo pedido."""
        from src.models.user_models import Role

        ya_admin, _ = create_user(
            f"yaadmin_{__import__('uuid').uuid4().hex[:8]}@example.com", roles=["admin"]
        )
        admin_role_id = self._admin_role_id(db_session)
        otro_rol = db_session.query(Role).filter(Role.rol != "admin").first()

        resp = client.put(
            f"/admin_user/users/{ya_admin.id}/roles",
            headers=admin_headers,
            json={"add": [admin_role_id, otro_rol.id], "remove": []},
        )
        assert resp.status_code == 200
