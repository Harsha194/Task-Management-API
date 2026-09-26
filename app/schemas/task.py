from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatusValues = Literal["pending", "in_progress", "completed"]
PriorityValues = Literal["low", "medium", "high"]


class TaskCreate(BaseModel):
    """Schema used to create a new task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    status: StatusValues = "pending"
    priority: PriorityValues = "medium"
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    """Schema used to update an existing task with partial values."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    status: StatusValues | None = None
    priority: PriorityValues | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    """Safe task data returned from the API."""

    id: str
    user_id: str
    title: str
    description: str
    status: StatusValues
    priority: PriorityValues
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """Paginated list of tasks for the authenticated user."""

    items: list[TaskResponse]
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)
    total: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class TaskAnalyticsResponse(BaseModel):
    """Aggregated statistics for the authenticated user's tasks."""

    total_tasks: int = Field(ge=0)
    completed_tasks: int = Field(ge=0)
    pending_tasks: int = Field(ge=0)
    in_progress_tasks: int = Field(ge=0)
    low_priority_tasks: int = Field(ge=0)
    medium_priority_tasks: int = Field(ge=0)
    high_priority_tasks: int = Field(ge=0)
    completion_rate: float = Field(ge=0.0, le=100.0)

    model_config = ConfigDict(from_attributes=True)
