from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Task(BaseModel):
    """Task document model used for application-level validation."""

    id: str | None = None
    user_id: str
    title: str
    description: str
    status: str
    priority: str
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
