# tests/test_tipo_cuenta.py
"""Tipo de cuenta (ciudadano / equipo). Ver
docs/superpowers/specs/2026-09-24-cuentas-de-equipo-design.md.

No se importa `src.*` a nivel de modulo: conftest levanta Postgres al importarse.
"""
import importlib.util
import pathlib
import uuid


def _migracion():
    ruta = pathlib.Path(__file__).parents[1] / "alembic/versions/a9b8c7d6e5f4_tipo_cuenta.py"
    spec = importlib.util.spec_from_file_location("migracion_tipo_cuenta", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_es_rol_de_equipo():
    from src.rbac import es_rol_de_equipo

    assert not es_rol_de_equipo("user")
    assert not es_rol_de_equipo("estudiante")
    assert es_rol_de_equipo("gestor_fomento")
    assert es_rol_de_equipo("un_rol_personalizado")


def test_la_migracion_convierte_las_cuentas_mixtas(db_session):
    from src.models.user_models import Role, User

    def rol(nombre):
        r = db_session.query(Role).filter(Role.rol == nombre).first()
        if not r:
            r = Role(rol=nombre)
            db_session.add(r)
            db_session.flush()
        return r

    mixta = User(email=f"mixta-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    mixta.roles = [rol("user"), rol("gestor_fomento")]
    ciudadana = User(email=f"ciu-{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", is_active=True)
    ciudadana.roles = [rol("user")]
    db_session.add_all([mixta, ciudadana])
    db_session.commit()

    convertidas = _migracion()._convertir_cuentas_de_equipo(db_session.connection())
    db_session.commit()
    db_session.expire_all()

    assert mixta.id in convertidas and ciudadana.id not in convertidas
    assert mixta.tipo_cuenta == "equipo"
    assert {r.rol for r in mixta.roles} == {"gestor_fomento"}
    assert ciudadana.tipo_cuenta == "ciudadano"
    assert {r.rol for r in ciudadana.roles} == {"user"}
