"""
Script para generar documentos de prueba para los usuarios creados en seed.py

Este script crea archivos de ejemplo en las rutas correctas para que
los usuarios de prueba puedan visualizar sus documentos en el dashboard.
"""
import os
import uuid
import sys
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal
from src.models.user_models import User
from src.models.persona_fisica_model import PersonaFisica
from src.models.persona_juridica_model import PersonaJuridica

# Directorio base para uploads (debe coincidir con upload_routes.py)
# Usar path local para desarrollo
if os.name == 'nt':  # Windows
    UPLOAD_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
else:
    UPLOAD_BASE_DIR = "/app/uploads"

def get_user_upload_dir(user_id: str) -> str:
    """Obtener el directorio de uploads para un usuario específico"""
    return os.path.join(UPLOAD_BASE_DIR, user_id)

def create_sample_file(filepath: str, title: str, extension: str):
    """Crear un archivo de ejemplo simple (texto o PDF si está disponible)"""
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if extension.lower() == '.pdf':
        try:
            # Intentar crear PDF si reportlab está disponible
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, height - inch, title)
            
            c.setFont("Helvetica", 12)
            y_position = height - 2 * inch
            
            c.drawString(inch, y_position, "Documento de ejemplo generado automáticamente")
            y_position -= 0.5 * inch
            c.drawString(inch, y_position, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            y_position -= 0.5 * inch
            c.drawString(inch, y_position, f"ID único: {uuid.uuid4().hex[:8]}")
            y_position -= 0.5 * inch
            c.drawString(inch, y_position, "Este es un documento de prueba para el sistema RePA.")
            
            c.save()
            return True
        except ImportError:
            # Si no hay reportlab, crear un archivo de texto con extensión .txt
            filepath = filepath.replace('.pdf', '.txt')
    
    if extension.lower() in ['.docx', '.txt'] or filepath.endswith('.txt'):
        try:
            # Intentar crear DOCX si python-docx está disponible
            if extension.lower() == '.docx' and not filepath.endswith('.txt'):
                from docx import Document
                
                doc = Document()
                doc.add_heading(title, 0)
                
                p = doc.add_paragraph('Documento de ejemplo generado automáticamente\n\n')
                p.add_run(f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
                p.add_run(f'ID único: {uuid.uuid4().hex[:8]}\n\n')
                p.add_run('Este es un documento de prueba para el sistema RePA.')
                
                doc.save(filepath)
                return True
        except ImportError:
            # Si no hay python-docx, crear un archivo de texto
            filepath = filepath.replace('.docx', '.txt')
    
    # Crear archivo de texto como fallback
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"{title}\n")
        f.write("=" * len(title) + "\n\n")
        f.write("Documento de ejemplo generado automáticamente\n\n")
        f.write(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"ID único: {uuid.uuid4().hex[:8]}\n\n")
        f.write("Este es un documento de prueba para el sistema RePA.\n")
        f.write(f"\nFormato original solicitado: {extension}")
    
    return True

def generate_documents():
    """Generar documentos para todos los usuarios que tengan registros"""
    db = SessionLocal()
    
    try:
        # Generar DNI para Persona Física
        print("Generando DNIs para Persona Física...")
        personas_fisicas = db.query(PersonaFisica).filter(
            PersonaFisica.dni_adjunto_path.is_(None)
        ).all()
        
        for pf in personas_fisicas:
            user = db.query(User).filter(User.id == pf.user_id).first()
            if user:
                filename = f"DNI_{pf.apellido}_{pf.nombre}_{uuid.uuid4().hex[:8]}.pdf"
                filepath = os.path.join(get_user_upload_dir(pf.user_id), filename)
                
                # Crear el archivo
                create_sample_file(filepath, f"DNI - {pf.nombre} {pf.apellido}", '.pdf')
                
                # Actualizar la base de datos con el nombre real del archivo
                actual_filename = os.path.basename(filepath)
                pf.dni_adjunto_path = actual_filename
                db.commit()
                
                print(f"  ✓ DNI creado para {user.email}: {actual_filename}")
        
        # Generar documentos para Persona Jurídica
        print("\nGenerando documentos para Persona Jurídica...")
        personas_juridicas = db.query(PersonaJuridica).filter(
            PersonaJuridica.estatuto_path.is_(None)
        ).all()
        
        for pj in personas_juridicas:
            user = db.query(User).filter(User.id == pj.user_id).first()
            if user:
                # Estatuto (PDF)
                filename = f"estatuto_{pj.razon_social}_{uuid.uuid4().hex[:8]}.pdf"
                filepath = os.path.join(get_user_upload_dir(pj.user_id), filename)
                create_sample_file(filepath, f"Estatuto - {pj.razon_social}", '.pdf')
                pj.estatuto_path = os.path.basename(filepath)
                
                # Constancia CUIT (PDF)
                filename = f"constancia_cuit_{pj.razon_social}_{uuid.uuid4().hex[:8]}.pdf"
                filepath = os.path.join(get_user_upload_dir(pj.user_id), filename)
                create_sample_file(filepath, f"Constancia CUIT - {pj.razon_social}", '.pdf')
                pj.constancia_cuit_path = os.path.basename(filepath)
                
                # Acta de Autoridades (DOCX)
                filename = f"acta_autoridades_{pj.razon_social}_{uuid.uuid4().hex[:8]}.docx"
                filepath = os.path.join(get_user_upload_dir(pj.user_id), filename)
                create_sample_file(filepath, f"Acta de Autoridades - {pj.razon_social}", '.docx')
                pj.acta_autoridades_path = os.path.basename(filepath)
                
                # CV Institucional (DOCX)
                filename = f"cv_institucional_{pj.razon_social}_{uuid.uuid4().hex[:8]}.docx"
                filepath = os.path.join(get_user_upload_dir(pj.user_id), filename)
                create_sample_file(filepath, f"CV Institucional - {pj.razon_social}", '.docx')
                pj.cv_institucional_path = os.path.basename(filepath)
                
                db.commit()
                
                print(f"  ✓ Documentos creados para {user.email}:")
                print(f"    - Estatuto: {pj.estatuto_path}")
                print(f"    - Constancia CUIT: {pj.constancia_cuit_path}")
                print(f"    - Acta de Autoridades: {pj.acta_autoridades_path}")
                print(f"    - CV Institucional: {pj.cv_institucional_path}")
        
        print("\n✅ Documentos generados exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error al generar documentos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Verificar que no estemos en producción
    from src.config import IS_PRODUCTION
    if IS_PRODUCTION:
        print("❌ Este script no debe ejecutarse en producción")
        exit(1)
    
    print("🚀 Iniciando generación de documentos de prueba...")
    print(f"Directorio de uploads: {UPLOAD_BASE_DIR}")
    
    # Crear directorio base si no existe
    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
    
    generate_documents()
