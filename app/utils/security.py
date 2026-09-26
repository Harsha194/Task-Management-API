from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify that a plain-text password matches a stored hash."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str | dict[str, str]) -> str:
    """Create a signed JWT bearer token for the provided subject."""
    if isinstance(subject, str):
        payload = {"sub": subject}
    else:
        payload = subject

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str]:
    """Decode and validate an access token, returning the claims payload."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid authentication credentials") from exc
