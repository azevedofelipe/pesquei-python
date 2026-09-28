from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Lure, User
from schemas.lure import LureCreate, LureResponse, LureUpdate
from security import get_current_user

router = APIRouter(
    prefix="/lure",
    tags=["lure"],
)


@router.get("/", response_model=list[LureResponse])
def list_lures(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Lure)
        .filter(Lure.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{lure_id}",response_model=LureResponse)
def get_lure(lure_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resultado = db.get(Lure, lure_id)

    if resultado is None or resultado.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lure not found")

    return resultado


@router.post("/", response_model=LureResponse, status_code=201)
def create_lure(
    lure: LureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    novo_lure = Lure(**lure.model_dump(), user_id=current_user.id)

    db.add(novo_lure)
    db.commit()
    db.refresh(novo_lure)

    return novo_lure


@router.patch("/{lure_id}", response_model=LureResponse)
def update_lure(
    lure_id: int,
    lure: LureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_lure = db.get(Lure, lure_id)

    if existing_lure is None or existing_lure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lure not found")

    for field, value in lure.model_dump(exclude_unset=True).items():
        setattr(existing_lure, field, value)

    db.commit()
    db.refresh(existing_lure)

    return existing_lure


@router.delete("/{lure_id}", status_code=204)
def delete_lure(
    lure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_lure = db.get(Lure, lure_id)

    if existing_lure is None or existing_lure.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lure not found")

    db.delete(existing_lure)
    db.commit()

    return Response(status_code=204)
