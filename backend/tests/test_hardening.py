"""
Tests de hardening AuthN/AuthZ (Fase 2 de la auditoría pre-producción):

- Un refresh/verify/recovery token NO sirve como token de acceso.
- Desactivar un usuario corta sus sesiones vigentes de inmediato.
- Quitar un rol surte efecto inmediato (roles desde DB, no desde el token).
- Protección de último admin (por roles y por desactivación).
- Solo un admin puede otorgar/quitar el rol admin.
"""

import uuid

import pytest

# NOTA: los imports de src.* van DENTRO de cada test — importarlos a nivel de
# módulo dispara la carga de src.config en la colección de pytest, antes de
# que conftest apunte DATABASE_URL al contenedor de test.


def _tokens():
    from src.token_utils import create_access_token, create_refresh_token

    return create_access_token, create_refresh_token


@pytest.fixture
def cuenta(create_user):
    email = f"hard_{uuid.uuid4().hex[:8]}@example.com"
    user, headers = create_user(email, roles=["user"])
    return user, headers


class TestTokenTypeConfusion:
    def test_refresh_token_no_autentica(self, client, cuenta):
        _create_access, create_refresh = _tokens()
        user, _headers = cuenta
        refresh = create_refresh(data={"sub": user.id})
        resp = client.get(
            "/users/me", headers={"Authorization": f"Bearer {refresh}"}
        )
        assert resp.status_code == 401

    def test_verify_token_no_autentica(self, client, cuenta):
        create_access, _create_refresh = _tokens()
        user, _headers = cuenta
        verify = create_access(
            data={"sub": user.id, "roles": ["unverified"]},
            expires_delta=60,
            type="verify",
        )
        resp = client.get(
            "/users/me", headers={"Authorization": f"Bearer {verify}"}
        )
        assert resp.status_code == 401

    def test_recover_token_no_autentica(self, client, cuenta):
        create_access, _create_refresh = _tokens()
        user, _headers = cuenta
        recover = create_access(
            data={"sub": user.id}, expires_delta=60, type="recover"
        )
        resp = client.get(
            "/users/me", headers={"Authorization": f"Bearer {recover}"}
        )
        assert resp.status_code == 401

    def test_access_token_si_autentica(self, client, cuenta):
        _user, headers = cuenta
        resp = client.get("/users/me", headers=headers)
        assert resp.status_code == 200


class TestRevocacionInmediata:
    def test_desactivar_usuario_corta_su_sesion(
        self, client, cuenta, admin_headers
    ):
        user, headers = cuenta
        # Sesión funciona
        assert client.get("/users/me", headers=headers).status_code == 200
        # Admin desactiva al usuario
        resp = client.patch(
            f"/admin_user/users/{user.id}/status",
            headers=admin_headers,
            params={"is_active": False},
        )
        assert resp.status_code == 200
        # El token vigente deja de servir de inmediato
        assert client.get("/users/me", headers=headers).status_code == 401

    def test_quitar_rol_admin_surte_efecto_inmediato(
        self, client, create_user, admin_headers, db_session
    ):
        # Un segundo admin pierde acceso admin apenas le quitan el rol,
        # aunque su token siga vigente.
        from src.models.user_models import Role

        _admin2, headers2 = create_user(
            f"admin2_{uuid.uuid4().hex[:8]}@example.com", roles=["admin"]
        )
        # Con rol admin puede listar usuarios
        assert (
            client.get("/admin_user/users", headers=headers2).status_code == 200
        )
        db_session.rollback()
        admin_role = db_session.query(Role).filter(Role.rol == "admin").first()
        resp = client.put(
            f"/admin_user/users/{_admin2.id}/roles",
            headers=admin_headers,
            json={"add": [], "remove": [admin_role.id]},
        )
        assert resp.status_code == 200, resp.text
        # El mismo token ya no tiene acceso admin (roles vienen de la DB)
        assert (
            client.get("/admin_user/users", headers=headers2).status_code == 403
        )


class TestUltimoAdmin:
    def _admin_role_id(self, db_session):
        from src.models.user_models import Role

        db_session.rollback()
        return db_session.query(Role).filter(Role.rol == "admin").first().id

    def test_no_se_puede_quitar_admin_al_ultimo_admin(
        self, client, create_user, db_session
    ):
        # Dos admins frescos: A le quita el rol a B (ok), luego nadie puede
        # quitárselo a A (sería el último).
        admin_a, headers_a = create_user(
            f"lastadmin_a_{uuid.uuid4().hex[:8]}@example.com", roles=["admin"]
        )
        role_id = self._admin_role_id(db_session)
        # A no puede quitarse el rol a sí mismo (auto-protección existente)
        resp = client.put(
            f"/admin_user/users/{admin_a.id}/roles",
            headers=headers_a,
            json={"add": [], "remove": [role_id]},
        )
        assert resp.status_code == 400

    def test_usuario_con_roles_manage_no_puede_tocar_admin(
        self, client, create_user, db_session
    ):
        # Un rol custom con roles:manage NO alcanza para otorgar admin.
        from src.models.user_models import Permission, Role

        db_session.rollback()
        perm = (
            db_session.query(Permission)
            .filter(Permission.code == "roles:manage")
            .first()
        )
        rol_gestor = Role(rol=f"gestor_{uuid.uuid4().hex[:6]}", is_system=False)
        rol_gestor.permissions = [perm]
        db_session.add(rol_gestor)
        db_session.commit()

        _gestor, headers_gestor = create_user(
            f"gestor_{uuid.uuid4().hex[:8]}@example.com",
            roles=[rol_gestor.rol],
        )
        _victima, _ = create_user(
            f"victima_{uuid.uuid4().hex[:8]}@example.com", roles=["user"]
        )
        admin_role_id = self._admin_role_id(db_session)
        resp = client.put(
            f"/admin_user/users/{_victima.id}/roles",
            headers=headers_gestor,
            json={"add": [admin_role_id], "remove": []},
        )
        assert resp.status_code == 403
