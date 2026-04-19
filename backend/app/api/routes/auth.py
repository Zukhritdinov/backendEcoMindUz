from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.api.deps import SessionDep, CurrentUser
from app.core import security
from app.models import User, RoleEnum
from app.schemas.user import Token, UserResponse, UserCreate

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: SessionDep):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    # The first user registered gets admin rights
    is_first = db.query(User).count() == 0
    role = RoleEnum.admin if is_first else RoleEnum.user
    
    user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer",
    )

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> Any:
    """
    Get current user profile
    """
    return current_user
