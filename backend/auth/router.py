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
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not password_supported_by_bcrypt(body.password):
        raise HTTPException(status_code=400, detail="Password is too long")
    u = create_email_user(db, body.email, body.password, name=body.name)
    return TokenOut(access_token=create_access_token(u.email))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = get_user_by_email(db, body.email)
    if not u or not u.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if u.is_google:
        raise HTTPException(
            status_code=401,
            detail="This account uses Google sign-in. Please use the Google button instead.",
        )
    if not verify_password(body.password, u.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(access_token=create_access_token(u.email))


@router.post("/google", response_model=TokenOut)
def google_auth(body: GoogleIn, db: Session = Depends(get_db)):
    info = verify_google_token(body.credential)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    u = get_or_create_google_user(db, info["email"], name=info.get("name", ""))
    return TokenOut(access_token=create_access_token(u.email))
