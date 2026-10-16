from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.models.user import User
from app.schemas.user import TokenOut, UserCreate, UserLogin, UserOut

router = APIRouter()


@router.post("/register", response_model=TokenOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được đăng ký. Hãy đăng nhập hoặc dùng email khác.")

    user = User(
        name=payload.name,
        email=email,
        password_hash=get_password_hash(payload.password),
        role="recruiter",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được đăng ký. Hãy đăng nhập hoặc dùng email khác.") from exc
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(str(payload.email).strip().lower(), payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
