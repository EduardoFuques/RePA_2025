"""
Script para actualizar la base de datos con los paths de los documentos generados
"""

import os
import sys

# Agregar el directorio src al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica

# Mapeo de user_id a los archivos generados
DOCUMENTOS_GENERADOS = {
    "4938043f-6619-4e55-b546-e40857b3b9a6": {  # admin@repa.gob.ar
        "dni_adjunto_path": "DNI_González_María_eb7525b8.pdf"
    },
    "12345678-1234-1234-1234-123456789012": {  # usuario1@repa.gob.ar
        "estatuto_path": "estatuto_Productora_Misionera_SRL_966ead23.pdf",
        "constancia_cuit_path": "constancia_cuit_Productora_Misionera_SRL_9fee7396.pdf",
        "acta_autoridades_path": "acta_autoridades_Productora_Misionera_SRL_acd4e73a.docx",
        "cv_institucional_path": "cv_institucional_Productora_Misionera_SRL_e2a7e55d.docx",
    },
    "87654321-4321-4321-4321-210987654321": {  # usuario2@repa.gob.ar
        "dni_adjunto_path": "DNI_Fernández_Luciana_03879222.pdf"
    },
    "11111111-1111-1111-1111-111111111111": {  # usuario3@repa.gob.ar
        "estatuto_path": "estatuto_Colectivo_Audiovisual_del_NEA_72d1450e.pdf",
        "constancia_cuit_path": "constancia_cuit_Colectivo_Audiovisual_del_NEA_5e370395.pdf",
        "acta_autoridades_path": "acta_autoridades_Colectivo_Audiovisual_del_NEA_023a972e.docx",
        "cv_institucional_path": "cv_institucional_Colectivo_Audiovisual_del_NEA_1ea46602.docx",
    },
}


def update_database():
    """Actualizar la base de datos con los paths de los documentos"""
    db = SessionLocal()

    try:
        print("🔄 Actualizando base de datos con los paths de documentos...")

        # Actualizar Persona Física
        for user_id, docs in DOCUMENTOS_GENERADOS.items():
            if "dni_adjunto_path" in docs:
                pf = (
                    db.query(PersonaFisica)
                    .filter(PersonaFisica.user_id == user_id)
                    .first()
                )
                if pf:
                    pf.dni_adjunto_path = docs["dni_adjunto_path"]
                    print(f"  ✓ DNI actualizado para user_id: {user_id}")

        # Actualizar Persona Jurídica
        for user_id, docs in DOCUMENTOS_GENERADOS.items():
            pj = (
                db.query(PersonaJuridica)
                .filter(PersonaJuridica.user_id == user_id)
                .first()
            )
            if pj:
                if "estatuto_path" in docs:
                    pj.estatuto_path = docs["estatuto_path"]
                if "constancia_cuit_path" in docs:
                    pj.constancia_cuit_path = docs["constancia_cuit_path"]
                if "acta_autoridades_path" in docs:
                    pj.acta_autoridades_path = docs["acta_autoridades_path"]
                if "cv_institucional_path" in docs:
                    pj.cv_institucional_path = docs["cv_institucional_path"]
                print(f"  ✓ Documentos PJ actualizados para user_id: {user_id}")

        db.commit()
        print("\n✅ Base de datos actualizada exitosamente!")

        # Verificar los datos
        print("\n📋 Verificación de datos actualizados:")
        for user_id, docs in DOCUMENTOS_GENERADOS.items():
            print(f"\nUser ID: {user_id}")
            for field, path in docs.items():
                print(f"  {field}: {path}")

    except Exception as e:
        print(f"\n❌ Error al actualizar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_database()
