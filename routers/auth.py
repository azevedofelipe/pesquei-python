from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.auth import Token
from schemas.user import UserCreate, UserResponse
from security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == user.email)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if db.scalar(select(User).where(User.username == user.username)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    novo_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        created_at=datetime.now(),
    )

    db.add(novo_user)
    db.commit()
    db.refresh(novo_user)

    return novo_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form_data.username))

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=access_token)
