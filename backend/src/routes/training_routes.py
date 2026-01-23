from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # PAra el debug de errores
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from typing import List

from src.models.user_models import User
from src.models.training_models import Training
from src.schemas.trainig_schemas import TrainingBase, TrainingCreate, TrainingOut, TrainingUpdate

from src.database import get_db
from src.utils import get_current_user

training_router = APIRouter()

# Crear un Training
@training_router.post("/create", response_model=TrainingOut, status_code=status.HTTP_201_CREATED, description="Crear un nuevo curso")
async def create_training(training_in: TrainingCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Crear un curso nuevo para el usuairo
    """
    # print(f"Current User is:{current_user}") # Debug
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )
    
    # Validar que la fecha de inicio sea manor que fecha finalización
    #if training_in.fecha_inicio >= training_in.fecha_finalizacion :
    #    raise HTTPException(
    #        status_code=status.HTTP_400_BAD_REQUEST,
    #        detail="Fecha Finalización es mayor o igual que Fecha de Inicio"
    #    )
    
    db_training = Training(**training_in.dict(), user_id=current_user["id"])
    db.add(db_training)
    db.commit()
    db.refresh(db_training)
    return db_training
    
# Update datos de Training
@training_router.put("/update/{training_id}", response_model=TrainingOut, status_code=status.HTTP_201_CREATED, description="Actualizar un curso")
async def update_training(training_id: int, training_in: TrainingCreate, current_user: dict= Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Actualizar los datos de un curso
    Args:
        training_in (dict): Diccionario con los datos de Curso para ser actualizado
    Return:
        TrainingOut (dict): Diccionario con los datos del curso actualizado
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado",
        )

    training = db.query(Training).filter(Training.id == training_id, Training.user_id == current_user["id"]).first()
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado",
        )

    for key, value in training_in.dict().items():
        setattr(training, key, value)

    db.commit()
    db.refresh(training)
    return training


# Read datos de Training
@training_router.get("/me/{training_id}", response_model=TrainingOut, status_code=status.HTTP_200_OK, description="Leer un curso")
async def get_training(training_id: int, current_user: dict= Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Recuperar los datos de un curso
    Args:
        training_id (int): Código de curso
    Return:
        TrainingOut (dict): Diccionario con los datos de un curso
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario No encontrado"
        )
    training = db.query(Training).filter(Training.id == training_id, Training.user_id == current_user["id"]).first()
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )
    return training

# Listar datos de Training
@training_router.get("/list", response_model=List[TrainingOut], status_code=status.HTTP_200_OK, description="Listar un curso")
async def get_list_training(current_user: dict= Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Listar todos los cursos del usuario
    Args:
        current_user.id (str): String con los datos del usuario
    Return:
        TrainingOut (List): Listado de todos los cursos que tiene el usuario.
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario No encontrado"
        )
    
    trainings = db.query(Training).filter(Training.user_id == current_user["id"]).all()
    if not trainings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cursos no encontrado"
        )
    return trainings

# Delete dato de Training
@training_router.delete("/delete/{training_id}", response_model=TrainingOut, status_code=status.HTTP_200_OK, description="Borrar un curso")
async def delete_training(training_id: int, current_user: dict=Depends(get_current_user), db: Session=Depends(get_db)):
    """
    Borrar un curso del usuario, 
    Args:
        training_id (int): Código de curso a borrar.
    """
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario No encontrado"
        )
    training = db.query(Training).filter(
        Training.id == training_id, 
        Training.user_id == current_user["id"]
    ).first()
    
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )
    
    try:
        # Eliminar el registro
        db.delete(training)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando training: {str(e)}"
        )
    return 
