# routes/esa_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.models.esa_model import EstudianteESA
from src.schemas.esa_schemas import EstudianteESACreate, EstudianteESAUpdate, EstudianteESAOut
from src.database import get_db
from src.utils import get_current_user

esa_router = APIRouter()


@esa_router.post("/", response_model=EstudianteESAOut, status_code=status.HTTP_201_CREATED)
async def create_estudiante_esa(
    data: EstudianteESACreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear registro de Estudiante ESA para el usuario actual"""
    # Verificar que el usuario no tenga ya un registro ESA
    existing = db.query(EstudianteESA).filter(EstudianteESA.user_id == current_user["id"]).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un registro de Estudiante ESA"
        )
    
    # Calcular fecha de vencimiento (1 año)
    fecha_alta = datetime.utcnow()
    fecha_vencimiento = fecha_alta + timedelta(days=365)
    
    db_estudiante = EstudianteESA(
        **data.model_dump(),
        user_id=current_user["id"],
        fecha_alta=fecha_alta,
        fecha_vencimiento=fecha_vencimiento
    )
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante


@esa_router.get("/me", response_model=EstudianteESAOut)
async def get_my_estudiante_esa(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el registro de Estudiante ESA del usuario actual"""
    estudiante = db.query(EstudianteESA).filter(EstudianteESA.user_id == current_user["id"]).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Estudiante ESA"
        )
    return estudiante


@esa_router.put("/me", response_model=EstudianteESAOut)
async def update_my_estudiante_esa(
    data: EstudianteESAUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar el registro de Estudiante ESA del usuario actual"""
    estudiante = db.query(EstudianteESA).filter(EstudianteESA.user_id == current_user["id"]).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Estudiante ESA"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(estudiante, key, value)
    
    db.commit()
    db.refresh(estudiante)
    return estudiante


@esa_router.post("/me/renovar", response_model=EstudianteESAOut)
async def renovar_estudiante_esa(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Renovar el registro de Estudiante ESA por un año más"""
    estudiante = db.query(EstudianteESA).filter(EstudianteESA.user_id == current_user["id"]).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Estudiante ESA"
        )
    
    # Renovar por un año desde hoy
    estudiante.fecha_vencimiento = datetime.utcnow() + timedelta(days=365)
    estudiante.activo = True
    
    db.commit()
    db.refresh(estudiante)
    return estudiante


@esa_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_estudiante_esa(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar el registro de Estudiante ESA del usuario actual"""
    estudiante = db.query(EstudianteESA).filter(EstudianteESA.user_id == current_user["id"]).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de Estudiante ESA"
        )
    
    db.delete(estudiante)
    db.commit()
    return None
