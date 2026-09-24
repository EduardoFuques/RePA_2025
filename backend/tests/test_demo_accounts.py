# tests/test_demo_accounts.py
"""GET /users/demo-accounts: credenciales de prueba para el login de QA.

Antes iban compiladas en el bundle del frontend. Ahora las entrega el
backend, y solo donde esos usuarios existen: el endpoint tiene que negarse
sin SEED_DEMO_DATA y, sobre todo, en produccion aunque SEED_DEMO_DATA este
activo.

No se importa `src.*` a nivel de modulo: conftest levanta el contenedor de
Postgres al importarse y los imports tienen que ocurrir despues.
"""

import pytest

URL = "/users/demo-accounts"


@pytest.fixture
def entorno(monkeypatch):
    """Fija IS_PRODUCTION / SEED_DEMO_DATA (el endpoint los lee al llamarse)."""
    import src.config as config

    def _fijar(produccion: bool, seed: bool):
        monkeypatch.setattr(config, "IS_PRODUCTION", produccion)
        monkeypatch.setattr(config, "SEED_DEMO_DATA", seed)

    return _fijar


def test_con_datos_demo_devuelve_las_cuentas_sin_autenticacion(client, entorno):
    entorno(produccion=False, seed=True)
    resp = client.get(URL)
    assert resp.status_code == 200, resp.text
    cuentas = resp.json()
    # 2 por cada uno de los 8 roles + 2 estudiantes.
    assert len(cuentas) == 18
    assert {c["rol"] for c in cuentas} == {
        "admin", "gestor_fomento", "evaluador", "revisor_padron",
        "lectura", "user", "gestor_administracion", "gestor_juridico",
        "estudiante",
    }
    assert {"rol", "email", "password"} <= set(cuentas[0])


def test_sin_datos_demo_es_404(client, entorno):
    entorno(produccion=False, seed=False)
    assert client.get(URL).status_code == 404


def test_en_produccion_es_404_aunque_haya_datos_demo(client, entorno):
    entorno(produccion=True, seed=True)
    assert client.get(URL).status_code == 404


def test_son_las_mismas_cuentas_que_crea_el_seed():
    """Una sola lista: el endpoint no puede ofrecer un usuario que el seed no crea."""
    from src.demo_users import TEST_ESA_USERS, TEST_ROLE_USERS, cuentas_demo
    from src.seed import TEST_ROLE_USERS as SEED_ROLE_USERS

    assert SEED_ROLE_USERS is TEST_ROLE_USERS
    emails_seed = {e for us in TEST_ROLE_USERS.values() for e, _ in us}
    emails_seed |= {e for e, _ in TEST_ESA_USERS}
    assert {c["email"] for c in cuentas_demo()} == emails_seed
