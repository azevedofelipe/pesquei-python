from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Catch, User
from schemas.catch import CatchCreate, CatchResponse
from security import get_current_user

router = APIRouter(
    prefix="/catch",
    tags=["catch"],
)


@router.get("/{catch_id}",response_model=CatchResponse)
def get_catch(catch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resultado = db.get(Catch, catch_id)

    if resultado is None or resultado.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Catch not found")

    return resultado


@router.post("/")
def create_catch(catch: CatchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    novo_catch = Catch(**catch.model_dump(), user_id=current_user.id)

    db.add(novo_catch)
    db.commit()
    db.refresh(novo_catch)

    return novo_catch