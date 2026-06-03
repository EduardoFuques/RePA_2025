"""
Tests del módulo de RBAC: permisos, roles, gestión de usuarios y auditoría.

Cubre:
- Regresión del bug de routing: /admin_user/audit-logs debe ser alcanzable.
- Enforcement de permisos (401 sin token, 403 sin permiso, 200 con admin).
- CRUD de roles y protección de roles del sistema.
- Auto-protección del administrador.
"""
# Las fixtures `rbac_seeded`, `admin_headers`, `user_headers` y `create_user`
# están centralizadas en conftest.py (infraestructura compartida).


class TestAuditLogsRouting:
    def test_audit_logs_reachable_for_admin(self, client, admin_headers):
        # Regresión: antes /{user_id} ocultaba /audit-logs (devolvía 404)
        resp = client.get("/admin_user/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPermissionEnforcement:
    def test_users_requires_auth(self, client):
        resp = client.get("/admin_user/users")
        assert resp.status_code == 401

    def test_users_forbidden_for_regular_user(self, client, user_headers):
        resp = client.get("/admin_user/users", headers=user_headers)
        assert resp.status_code == 403

    def test_users_allowed_for_admin(self, client, admin_headers):
        resp = client.get("/admin_user/users", headers=admin_headers)
        assert resp.status_code == 200

    def test_my_permissions_admin_has_all(self, client, admin_headers):
        resp = client.get("/users/me/permissions", headers=admin_headers)
        assert resp.status_code == 200
        from src.rbac import ALL_PERMISSIONS

        assert set(resp.json()) == set(ALL_PERMISSIONS)


class TestRoleManagement:
    def test_list_roles_includes_system_roles(self, client, admin_headers):
        resp = client.get("/admin_user/roles", headers=admin_headers)
        assert resp.status_code == 200
        nombres = {r["rol"] for r in resp.json()}
        assert {"admin", "user", "gestor_fomento"}.issubset(nombres)

    def test_create_and_delete_custom_role(self, client, admin_headers):
        resp = client.post(
            "/admin_user/roles",
            headers=admin_headers,
            json={
                "rol": "rol_test_custom",
                "descripcion": "Rol de prueba",
                "permissions": ["users:read"],
            },
        )
        assert resp.status_code == 201, resp.text
        role = resp.json()
        assert role["is_system"] is False
        assert [p["code"] for p in role["permissions"]] == ["users:read"]

        del_resp = client.delete(
            f"/admin_user/roles/{role['id']}", headers=admin_headers
        )
        assert del_resp.status_code == 204

    def test_cannot_delete_system_role(self, client, admin_headers):
        roles = client.get("/admin_user/roles", headers=admin_headers).json()
        admin_role = next(r for r in roles if r["rol"] == "admin")
        resp = client.delete(
            f"/admin_user/roles/{admin_role['id']}", headers=admin_headers
        )
        assert resp.status_code == 400

    def test_create_role_with_invalid_permission(self, client, admin_headers):
        resp = client.post(
            "/admin_user/roles",
            headers=admin_headers,
            json={"rol": "rol_invalido", "permissions": ["no:existe"]},
        )
        assert resp.status_code == 400


class TestAdminSelfProtection:
    def test_admin_cannot_deactivate_self(self, client, admin_headers, db_session):
        from src.models.user_models import User

        admin = (
            db_session.query(User)
            .filter(User.email == "admin_rbac@example.com")
            .first()
        )
        resp = client.patch(
            f"/admin_user/users/{admin.id}/status?is_active=false",
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestStartupSmoke:
    def test_health_endpoints(self, client):
        # La app levantó (lifespan ejecutó create_all/migraciones + seed sin excepción)
        resp = client.get("/health")
        assert resp.status_code == 200
        resp_live = client.get("/health/live")
        assert resp_live.status_code == 200
        resp_ready = client.get("/health/ready")
        assert resp_ready.status_code == 200
