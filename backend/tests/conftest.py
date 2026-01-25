# tests/conftest.py
import os
import pytest
from testcontainers.postgres import PostgresContainer

# Variable global para el engine (se configura en el fixture de sesión)
_engine = None
_TestingSessionLocal = None
_postgres_url = None


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    """Levanta un contenedor PostgreSQL para toda la sesión de tests"""
    global _postgres_url
    with PostgresContainer("postgres:15-alpine") as postgres:
        _postgres_url = postgres.get_connection_url()
        # Configurar variable de entorno ANTES de importar la app
        os.environ["DATABASE_URL"] = _postgres_url
        yield postgres


@pytest.fixture(scope="session")
def engine(postgres_container):
    """Crea el engine de SQLAlchemy conectado al contenedor PostgreSQL"""
    global _engine
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
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
    from src.main import app
    from src.database import get_db
    
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
