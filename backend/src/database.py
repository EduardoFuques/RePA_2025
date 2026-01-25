from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL)  # ← ,echo True ¡Habilita logs!
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Crear tablas en la base de datos
def init_db():
    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)

# Dependencia para obtener sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()