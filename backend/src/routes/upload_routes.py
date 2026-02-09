from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from datetime import datetime
from ..database import get_db
from ..utils import get_current_user
upload_router = APIRouter(prefix="/upload", tags=["upload"])

# Alias para compatibilidad con frontend que usa /api/files
files_router = APIRouter(prefix="/files", tags=["files"])

# Directorio base para uploads
UPLOAD_BASE_DIR = "/app/uploads"

def get_user_upload_dir(user_id: str) -> str:
    """Obtener el directorio de uploads para un usuario específico"""
    return os.path.join(UPLOAD_BASE_DIR, user_id)

def ensure_user_dir(user_id: str):
    """Asegurar que exista el directorio del usuario"""
    user_dir = get_user_upload_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

@upload_router.post("/dni")
async def upload_dni(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Subir el archivo DNI del usuario
    """
    # Validar tipo de archivo
    if not file.content_type or not file.content_type.startswith('application/'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    
    # Validar tamaño (máximo 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="El archivo no puede superar los 5MB")
    
    # Reiniciar el puntero del archivo
    await file.seek(0)
    
    # Crear directorio del usuario si no existe
    user_id = current_user["id"]
    user_dir = ensure_user_dir(user_id)
    
    # Generar nombre único para el archivo
    file_extension = os.path.splitext(file.filename)[1]
    if file_extension.lower() != '.pdf':
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    
    unique_filename = f"dni_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(user_dir, unique_filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")
    
    # Devolver la ruta relativa del archivo
    relative_path = os.path.join(user_id, unique_filename)
    
    return JSONResponse({
        "message": "Archivo subido exitosamente",
        "path": relative_path,
        "filename": unique_filename
    })

ALLOWED_DOC_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
ALLOWED_DOC_TYPES = {
    'estatuto': {'extensions': {'.pdf', '.jpg', '.jpeg', '.png'}, 'max_size': 5 * 1024 * 1024},
    'constancia_cuit': {'extensions': {'.pdf', '.jpg', '.jpeg', '.png'}, 'max_size': 5 * 1024 * 1024},
    'acta_autoridades': {'extensions': {'.pdf', '.jpg', '.jpeg', '.png'}, 'max_size': 5 * 1024 * 1024},
    'cv_institucional': {'extensions': {'.pdf', '.doc', '.docx'}, 'max_size': 10 * 1024 * 1024},
}

MIME_MAP = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

@upload_router.post("/document/{doc_type}")
async def upload_document(
    doc_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Subir un documento genérico (estatuto, constancia_cuit, acta_autoridades, cv_institucional)
    """
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de documento no válido: {doc_type}")
    
    doc_config = ALLOWED_DOC_TYPES[doc_type]
    
    # Validar extensión
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in doc_config['extensions']:
        allowed = ', '.join(doc_config['extensions'])
        raise HTTPException(status_code=400, detail=f"Extensión no permitida. Permitidas: {allowed}")
    
    # Validar tamaño
    file_content = await file.read()
    if len(file_content) > doc_config['max_size']:
        max_mb = doc_config['max_size'] // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"El archivo no puede superar los {max_mb}MB")
    
    await file.seek(0)
    
    # Crear directorio del usuario
    user_id = current_user["id"]
    user_dir = ensure_user_dir(user_id)
    
    # Generar nombre único
    unique_filename = f"{doc_type}_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = os.path.join(user_dir, unique_filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")
    
    relative_path = os.path.join(user_id, unique_filename)
    
    return JSONResponse({
        "message": "Archivo subido exitosamente",
        "path": relative_path,
        "filename": unique_filename
    })

@upload_router.get("/document/{filepath:path}")
async def get_document(
    filepath: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Obtener un documento subido por el usuario
    """
    from fastapi.responses import FileResponse
    
    user_id = current_user["id"]
    
    # Validar que el archivo pertenezca al usuario
    if '/' in filepath:
        file_user_id = filepath.split('/')[0]
        if file_user_id != user_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        file_path = os.path.join(UPLOAD_BASE_DIR, filepath)
    else:
        file_path = os.path.join(get_user_upload_dir(user_id), filepath)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Determinar media type
    file_extension = os.path.splitext(file_path)[1].lower()
    media_type = MIME_MAP.get(file_extension, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filepath.split('/')[-1]
    )

@upload_router.delete("/dni/{filename}")
async def delete_dni(
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Eliminar un archivo DNI del usuario
    """
    user_id = current_user["id"]
    file_path = os.path.join(get_user_upload_dir(user_id), filename)
    
    # Validar que el archivo exista
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Eliminar archivo
    try:
        os.remove(file_path)
        return JSONResponse({"message": "Archivo eliminado exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el archivo: {str(e)}")

@upload_router.get("/dni/{filename:path}")
async def get_dni(
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Obtener un archivo DNI del usuario
    filename puede ser solo el nombre o la ruta completa (user_id/filename)
    """
    user_id = current_user["id"]
    
    # Si filename incluye una barra, asumimos que es la ruta completa
    if '/' in filename:
        # Validar que el archivo pertenezca al usuario
        file_user_id = filename.split('/')[0]
        if file_user_id != user_id:
            raise HTTPException(status_code=403, detail="No autorizado")
        file_path = os.path.join(UPLOAD_BASE_DIR, filename)
    else:
        # Es solo el nombre del archivo
        file_path = os.path.join(get_user_upload_dir(user_id), filename)
    
    # Validar que el archivo exista
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Devolver archivo
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename.split('/')[-1]  # Solo el nombre del archivo
    )

@upload_router.get("/my-dni")
async def get_my_dni(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Obtener el DNI del usuario actual (si existe)
    """
    from ..models.persona_fisica_model import PersonaFisica
    
    print(f"[DEBUG] get_my_dni - user_id: {current_user['id']}, email: {current_user.get('email', 'N/A')}")
    
    # Buscar el DNI en la base de datos
    persona = db.query(PersonaFisica).filter(
        PersonaFisica.user_id == current_user["id"]
    ).first()
    
    if not persona or not persona.dni_adjunto_path:
        print(f"[DEBUG] No DNI found for user {current_user['id']}")
        raise HTTPException(status_code=404, detail="No hay DNI adjunto")
    
    print(f"[DEBUG] DNI path from DB: {persona.dni_adjunto_path}")
    
    # Construir la ruta completa incluyendo el user_id
    file_path = os.path.join(UPLOAD_BASE_DIR, current_user["id"], persona.dni_adjunto_path)
    print(f"[DEBUG] Full file path: {file_path}")
    
    # Validar que el archivo exista
    if not os.path.exists(file_path):
        print(f"[DEBUG] File not found at: {file_path}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    print(f"[DEBUG] Serving file: {file_path}")
    
    # Devolver archivo
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=persona.dni_adjunto_path.split('/')[-1]
    )


# Endpoint compatibilidad para /api/files/view
@files_router.get("/view/{filepath:path}")
async def view_file(
    filepath: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Ver un archivo del usuario autenticado
    """
    import urllib.parse
    filepath = urllib.parse.unquote(filepath)
    
    # Buscar en el directorio del usuario autenticado
    user_dir = os.path.join(UPLOAD_BASE_DIR, current_user["id"])
    file_path = os.path.join(user_dir, filepath)
    
    if os.path.exists(file_path):
        # Determinar media type
        if filepath.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filepath.lower().endswith(('.jpg', '.jpeg')):
            media_type = 'image/jpeg'
        elif filepath.lower().endswith('.png'):
            media_type = 'image/png'
        elif filepath.lower().endswith('.docx'):
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            media_type = 'application/octet-stream'
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename=\"{filepath}\""}
        )
    
    raise HTTPException(status_code=404, detail="Archivo no encontrado")


@files_router.get("/download/{filepath:path}")
async def download_file(
    filepath: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Descargar un archivo del usuario autenticado
    """
    import urllib.parse
    filepath = urllib.parse.unquote(filepath)
    
    # Buscar en el directorio del usuario autenticado
    user_dir = os.path.join(UPLOAD_BASE_DIR, current_user["id"])
    file_path = os.path.join(user_dir, filepath)
    
    if os.path.exists(file_path):
        # Determinar media type
        if filepath.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filepath.lower().endswith(('.jpg', '.jpeg')):
            media_type = 'image/jpeg'
        elif filepath.lower().endswith('.png'):
            media_type = 'image/png'
        elif filepath.lower().endswith('.docx'):
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            media_type = 'application/octet-stream'
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=\"{filepath}\""}
        )
    
    raise HTTPException(status_code=404, detail="Archivo no encontrado")
