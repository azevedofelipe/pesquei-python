from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Catch
from schemas import CatchCreate, CatchResponse

router = APIRouter(
    prefix="/catch",
    tags=["catch"],
)


@router.get("/{catch_id}",response_model=CatchResponse)
def get_catch(catch_id: int, db: Session = Depends(get_db)):
    resultado = db.get(Catch, catch_id)

    if resultado is None:
        raise HTTPException(status_code=404, detail="Catch not found")

    return resultado


@router.post("/")
def create_catch(catch: CatchCreate, db: Session = Depends(get_db)):
    novo_catch = Catch(**catch.model_dump())

    db.add(novo_catch)
    db.commit()
    db.refresh(novo_catch)

    return novo_catch