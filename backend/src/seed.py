from src.database import init_db, SessionLocal
from src.models.user_models import Role
from sqlalchemy.exc import IntegrityError

def seed_data():
    # Inicializa las tablas
    init_db()

    db = SessionLocal()
    try:
        # Verifica si ya existen roles
        if not db.query(Role).first():
            roles = [
                Role(rol="admin"),
                Role(rol="user")
            ]
            db.add_all(roles)
            db.commit()
            # Seed de roles completado
        else:
            pass  # Los roles ya existen
    except IntegrityError as e:
        db.rollback()
        # Error insertando seed - se ignora si ya existen
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()