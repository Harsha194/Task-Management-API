from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User document model used for application-level validation."""

    id: str | None = None
    name: str
    email: EmailStr
    password_hash: str
    created_at: datetime
    updated_at: datetime
