from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.deps import get_db
from auth.schemas import GoogleIn, LoginIn, RegisterIn, TokenOut
from auth.service import (
    create_access_token,
    create_email_user,
    get_or_create_google_user,
    get_user_by_email,
    password_supported_by_bcrypt,
    verify_google_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    if not password_supported_by_bcrypt(body.password):
        raise HTTPException(status_code=400, detail="Password too long")
    u = create_email_user(db, body.email, body.password)
    return TokenOut(access_token=create_access_token(u.email))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = get_user_by_email(db, body.email)
    if not u or u.is_google or not u.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, u.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(access_token=create_access_token(u.email))


@router.post("/google", response_model=TokenOut)
def google_auth(body: GoogleIn, db: Session = Depends(get_db)):
    email = verify_google_token(body.credential)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    u = get_or_create_google_user(db, email)
    return TokenOut(access_token=create_access_token(u.email))
