# tests/test_seed_cuentas.py
"""Seed: el equipo sin registro RePA, los ciudadanos con el padron demo, y
los emails diciendo que es cada cuenta.

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""


def test_emails_dicen_que_son():
    from src.demo_users import CIUDADANOS_PADRON, TEST_ESA_USERS, TEST_ROLE_USERS

    for rol, usuarios in TEST_ROLE_USERS.items():
        prefijo = "ciudadano." if rol == "user" else "equipo."
        assert all(email.startswith(prefijo) for email, _ in usuarios), rol
    assert all(e.startswith("ciudadano.estudiante") for e, _ in TEST_ESA_USERS)
    assert len(CIUDADANOS_PADRON) == 10
    assert all(e.startswith("ciudadano.padron") for e in CIUDADANOS_PADRON)


def test_el_seed_deja_al_equipo_sin_registros_y_al_padron_en_ciudadanos(db_session):
    from src.demo_users import (
        CIUDADANOS_EVALUADORES,
        CIUDADANOS_PADRON,
        TEST_ROLE_USERS,
    )
    from src.models.fomento_model import Evaluador
    from src.models.persona_fisica_model import PersonaFisica
    from src.models.user_models import User
    from src.seed import seed_fomento_data, seed_padron_data, seed_test_users, sync_rbac

    sync_rbac(db_session)
    seed_test_users(db_session)
    seed_padron_data(db_session)
    seed_fomento_data(db_session)

    for rol, usuarios in TEST_ROLE_USERS.items():
        for email, _ in usuarios:
            u = db_session.query(User).filter(User.email == email).first()
            assert u.tipo_cuenta == ("ciudadano" if rol == "user" else "equipo"), email
            if rol != "user":
                assert db_session.query(PersonaFisica).filter(PersonaFisica.user_id == u.id).first() is None, email
                assert db_session.query(Evaluador).filter(Evaluador.user_id == u.id).first() is None, email
    for email in CIUDADANOS_PADRON:
        u = db_session.query(User).filter(User.email == email).first()
        assert u.tipo_cuenta == "ciudadano"
        assert db_session.query(PersonaFisica).filter(PersonaFisica.user_id == u.id).first() is not None, email
    for email in CIUDADANOS_EVALUADORES:
        u = db_session.query(User).filter(User.email == email).first()
        assert db_session.query(Evaluador).filter(Evaluador.user_id == u.id).first() is not None, email


def test_seed_idempotente(db_session):
    from src.models.user_models import User
    from src.seed import seed_padron_data, seed_test_users, sync_rbac

    sync_rbac(db_session)
    seed_test_users(db_session)
    antes = db_session.query(User).count()
    seed_test_users(db_session)
    seed_padron_data(db_session)
    assert db_session.query(User).count() == antes
