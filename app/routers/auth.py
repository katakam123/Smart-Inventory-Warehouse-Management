from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.dependencies import get_current_user
from app.auth.jwt import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.auth.permissions import require_roles
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    data: UserRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    require_roles(
        current_user,
        ["Admin"]
    )

    existing_user = db.query(User).filter(
        (User.username == data.username)
        | (User.email == data.email)
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(
            data.password
        ),
        role=data.role,
        warehouse_id=data.warehouse_id,
        created_by=current_user.id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user



@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):

    return current_user