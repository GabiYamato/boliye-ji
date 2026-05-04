from datetime import datetime, timedelta, timezone

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

import config
from auth.models import User


def password_supported_by_bcrypt(p: str) -> bool:
    # bcrypt supports up to 72 bytes; enforce this before hashing.
    return len(p.encode("utf-8")) <= 72


def hash_password(p: str) -> str:
    if not password_supported_by_bcrypt(p):
        raise ValueError("Password is too long for bcrypt")
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(p: str, hashed: str) -> bool:
    if not password_supported_by_bcrypt(p):
        return False
    try:
        return bcrypt.checkpw(p.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": sub, "exp": exp},
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def create_email_user(db: Session, email: str, password: str, name: str = "") -> User:
    u = User(
        email=email.lower(),
        name=name.strip(),
        hashed_password=hash_password(password),
        is_google=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def get_or_create_google_user(db: Session, email: str, name: str = "") -> User:
    u = get_user_by_email(db, email)
    if u:
        return u
    u = User(
        email=email.lower(),
        name=name.strip() or email.split("@")[0],
        hashed_password=None,
        is_google=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def verify_google_token(credential: str) -> dict | None:
    """Verify Google ID token and return {email, name} or None."""
    if not config.GOOGLE_CLIENT_ID:
        return None
    try:
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            config.GOOGLE_CLIENT_ID,
        )
        email = info.get("email")
        if not email:
            return None
        return {
            "email": str(email).lower(),
            "name": str(info.get("name", "")),
        }
    except ValueError:
        return None
