from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Lure, User
from schemas.lure import LureCreate, LureResponse
from security import get_current_user

router = APIRouter(
    prefix="/lure",
    tags=["lure"],
)


@router.get("/{lure_id}",response_model=LureResponse)
def get_lure(lure_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resultado = db.get(Lure, lure_id)

    if resultado is None or resultado.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lure not found")

    return resultado


@router.post("/")
def create_catch(lure: LureCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    novo_lure = Lure(**lure.model_dump(), user_id=current_user.id)

    db.add(novo_lure)
    db.commit()
    db.refresh(novo_lure)

    return novo_lure