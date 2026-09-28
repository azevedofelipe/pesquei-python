from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Catch, User
from schemas.catch import CatchCreate, CatchResponse, CatchUpdate
from security import get_current_user

router = APIRouter(
    prefix="/catch",
    tags=["catch"],
)


@router.get("/", response_model=list[CatchResponse])
def list_catches(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Catch)
        .filter(Catch.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
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


@router.patch("/{catch_id}", response_model=CatchResponse)
def update_catch(
    catch_id: int,
    catch: CatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_catch = db.get(Catch, catch_id)

    if existing_catch is None or existing_catch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Catch not found")

    for field, value in catch.model_dump(exclude_unset=True).items():
        setattr(existing_catch, field, value)

    db.commit()
    db.refresh(existing_catch)

    return existing_catch


@router.delete("/{catch_id}", status_code=204)
def delete_catch(
    catch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_catch = db.get(Catch, catch_id)

    if existing_catch is None or existing_catch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Catch not found")

    db.delete(existing_catch)
    db.commit()

    return Response(status_code=204)
