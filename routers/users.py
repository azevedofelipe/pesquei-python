from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.user import UserResponse
from security import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resultado = db.get(User, user_id)

    if resultado is None or resultado.id != current_user.id:
        raise HTTPException(status_code=404, detail="User not found")

    return resultado
