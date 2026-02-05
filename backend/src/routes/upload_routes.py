from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from datetime import datetime
from ..database import get_db
from ..dependencies import get_current_user
from ..config import get_settings

settings = get_settings()
upload_router = APIRouter(prefix="/upload", tags=["upload"])

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

@upload_router.get("/dni/{filename}")
async def get_dni(
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Obtener un archivo DNI del usuario
    """
    user_id = current_user["id"]
    file_path = os.path.join(get_user_upload_dir(user_id), filename)
    
    # Validar que el archivo exista
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Devolver archivo
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        filename=filename
    )
