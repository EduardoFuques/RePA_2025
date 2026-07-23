# tests/conftest.py
import os

import pytest
from passlib.context import CryptContext
from testcontainers.postgres import PostgresContainer

# Configurar variables de entorno ANTES de importar cualquier módulo
os.environ["TESTING"] = "true"
os.environ["CI"] = "true"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Variable global para el engine (se configura en el fixture de sesión)
_engine = None
_TestingSessionLocal = None

# El contenedor se levanta a NIVEL DE MÓDULO, no en un fixture: pytest importa
# conftest.py antes de recolectar los módulos de test, así DATABASE_URL ya
# apunta al contenedor cuando cualquier test importe src.* a nivel de módulo.
# (Con el fixture de sesión, un `from src...` top-level en un test file
# fijaba la URL del .env — host "db" — y toda la suite fallaba en cadena.)
_postgres_container = PostgresContainer("postgres:17-alpine")
_postgres_container.start()
_postgres_url = _postgres_container.get_connection_url()
os.environ["DATABASE_URL"] = _postgres_url


def pytest_sessionfinish(session, exitstatus):
    """Apaga el contenedor al terminar la sesión de tests."""
    _postgres_container.stop()


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    """Contenedor PostgreSQL de la sesión (ya iniciado a nivel de módulo)."""
    yield _postgres_container


@pytest.fixture(scope="session")
def engine(postgres_container):
    """Crea el engine de SQLAlchemy conectado al contenedor PostgreSQL"""
    global _engine
    from sqlalchemy import create_engine

    # Importar el registry COMPLETO de modelos para que create_all cree
    # todas las tablas (incluido Fomento), sin depender del orden de imports.
    import src.models  # noqa: F401

    # Importar Base después de configurar DATABASE_URL
    from src.database import Base

    _engine = create_engine(_postgres_url)
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture(scope="session")
def SessionLocal(engine):
    """Crea el sessionmaker para tests"""
    global _TestingSessionLocal
    from sqlalchemy.orm import sessionmaker
    _TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _TestingSessionLocal


@pytest.fixture(scope="function")
def db_session(SessionLocal):
    """Proporciona una sesión de DB limpia para cada test"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def override_get_db():
    """Override de la dependencia de base de datos para tests"""
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(engine, SessionLocal):
    """Proporciona un cliente de test con PostgreSQL real"""
    from src.database import get_db
    from src.main import app

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def auth_headers(client, test_user_data, db_session):
    """Fixture que registra un usuario, lo activa y retorna headers de autenticación"""
    from src.models.user_models import User

    # Registrar usuario
    client.post("/users/register", json=test_user_data)

    # Activar usuario manualmente para tests (bypass verificación email)
    db_session.commit()  # Asegurar que el registro se guardó
    user = db_session.query(User).filter(User.email == test_user_data["email"]).first()
    if user:
        user.is_active = True
        db_session.commit()

    # Login para obtener token
    response = client.post(
        "/users/token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return {}


# ---------------------------------------------------------------------------
# Infraestructura compartida de RBAC / autenticación (reutilizable por suites)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def rbac_seeded(SessionLocal):
    """Sincroniza permisos y roles del sistema una vez para toda la sesión.

    Garantiza que los roles ('admin', 'user', 'gestor_fomento', ...) existan
    antes de cualquier test que cree usuarios con esos roles.
    """
    from src.seed import sync_rbac

    db = SessionLocal()
    try:
        sync_rbac(db)
    finally:
        db.close()


def _crear_usuario(db, email, password, roles=None):
    """Crea (idempotente) un usuario activo y le asigna los roles indicados."""
    from src.models.user_models import Role, User, UserRole

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=_pwd_context.hash(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    for rol in roles or []:
        role = db.query(Role).filter(Role.rol == rol).first()
        if role and not (
            db.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
            .first()
        ):
            db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def _login_headers(client, email, password):
    resp = client.post(
        "/users/token", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def create_user(client, db_session):
    """Factory para crear usuarios con roles. Retorna (user, headers)."""

    def _factory(email, password="Passw0rd!", roles=None):
        user = _crear_usuario(db_session, email, password, roles)
        headers = _login_headers(client, email, password)
        return user, headers

    return _factory


@pytest.fixture
def admin_headers(client, db_session):
    """Headers de un usuario con rol 'admin'."""
    _crear_usuario(db_session, "admin_rbac@example.com", "Admin1234", ["admin"])
    return _login_headers(client, "admin_rbac@example.com", "Admin1234")


@pytest.fixture
def user_headers(client, db_session):
    """Headers de un usuario regular con rol 'user'."""
    _crear_usuario(db_session, "user_rbac@example.com", "User1234", ["user"])
    return _login_headers(client, "user_rbac@example.com", "User1234")
