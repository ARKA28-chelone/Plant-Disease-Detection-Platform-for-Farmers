import os
import hmac
import time
import base64
import hashlib
import secrets
from typing import Optional

from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

# Secret used to sign login tokens; set AUTH_SECRET in production
SECRET_KEY = os.getenv("AUTH_SECRET", "plantcare-dev-secret-change-me").encode()
TOKEN_TTL_SECONDS = 7 * 24 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return hmac.compare_digest(check.hex(), digest)


def create_token(user_id: int) -> str:
    payload = f"{user_id}:{int(time.time()) + TOKEN_TTL_SECONDS}"
    sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def decode_token(token: str) -> Optional[int]:
    try:
        user_id, expires, sig = base64.urlsafe_b64decode(token.encode()).decode().split(":")
    except Exception:
        return None
    expected = hmac.new(SECRET_KEY, f"{user_id}:{expires}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected) or int(expires) < time.time():
        return None
    return int(user_id)


def get_optional_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Return the logged-in user if a valid Bearer token is sent, else None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = decode_token(authorization[7:])
    return db.get(User, user_id) if user_id else None


def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return user
