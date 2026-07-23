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
        body = resp.json()
        assert isinstance(body["items"], list)
        assert isinstance(body["total"], int)


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


class TestBecomeEstudiante:
    """Tests para POST /users/me/become-estudiante (auto-asignación del rol
    'estudiante', usado por la pantalla de elección al primer login)."""

    def test_list_roles_includes_estudiante(self, client, admin_headers):
        resp = client.get("/admin_user/roles", headers=admin_headers)
        assert resp.status_code == 200
        nombres = {r["rol"] for r in resp.json()}
        assert "estudiante" in nombres

    def test_requires_auth(self, client):
        resp = client.post("/users/me/become-estudiante")
        assert resp.status_code == 401

    def test_self_assigns_role(self, client, create_user):
        import uuid

        _user, headers = create_user(
            f"chooser_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
        )
        resp = client.post("/users/me/become-estudiante", headers=headers)
        assert resp.status_code == 200, resp.text
        roles = {r["rol"] for r in resp.json()["roles"]}
        assert "estudiante" in roles

    def test_idempotent(self, client, create_user, db_session):
        import uuid

        from src.models.user_models import Role, UserRole

        user, headers = create_user(
            f"chooser2_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
        )
        primero = client.post("/users/me/become-estudiante", headers=headers)
        segundo = client.post("/users/me/become-estudiante", headers=headers)
        assert primero.status_code == 200
        assert segundo.status_code == 200

        db_session.commit()
        estudiante_role = db_session.query(Role).filter(Role.rol == "estudiante").first()
        count = (
            db_session.query(UserRole)
            .filter(
                UserRole.user_id == user.id, UserRole.role_id == estudiante_role.id
            )
            .count()
        )
        assert count == 1

    def test_leaves_audit_trail(self, client, create_user, db_session):
        import uuid

        from src.models.audit_model import AuditAction, AuditLog

        user, headers = create_user(
            f"chooser3_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
        )
        resp = client.post("/users/me/become-estudiante", headers=headers)
        assert resp.status_code == 200

        db_session.commit()
        entry = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == AuditAction.ROLE_CHANGE,
                AuditLog.resource_type == "User",
            )
            .first()
        )
        assert entry is not None


class TestStartupSmoke:
    def test_health_endpoints(self, client):
        # La app levantó (lifespan ejecutó create_all/migraciones + seed sin excepción)
        resp = client.get("/health")
        assert resp.status_code == 200
        resp_live = client.get("/health/live")
        assert resp_live.status_code == 200
        resp_ready = client.get("/health/ready")
        assert resp_ready.status_code == 200
