from __future__ import annotations

from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.database import get_database
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.utils.security import create_access_token, hash_password, verify_password


def register_user(user_data: UserCreate) -> UserResponse:
    """Create a new user after validating the request and checking for duplicates."""
    users_collection = get_database()["users"]
    users_collection.create_index("email", unique=True)

    normalized_email = user_data.email.lower().strip()

    if users_collection.find_one({"email": normalized_email}):
        raise ValueError("Email already registered")

    now = datetime.now(timezone.utc)
    user_document = {
        "name": user_data.name.strip(),
        "email": normalized_email,
        "password_hash": hash_password(user_data.password),
        "created_at": now,
        "updated_at": now,
    }

    try:
        inserted = users_collection.insert_one(user_document)
    except DuplicateKeyError as exc:
        raise ValueError("Email already registered") from exc

    return UserResponse(
        id=str(inserted.inserted_id),
        name=user_document["name"],
        email=user_document["email"],
        created_at=user_document["created_at"],
        updated_at=user_document["updated_at"],
    )


def login_user(email: str, password: str) -> TokenResponse:
    """Validate login credentials and return a JWT access token."""
    users_collection = get_database()["users"]
    normalized_email = email.lower().strip()
    user = users_collection.find_one({"email": normalized_email})

    if user is None or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password")

    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token, token_type="bearer")
