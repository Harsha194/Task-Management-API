from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.database import get_database
from app.schemas.task import TaskAnalyticsResponse, TaskCreate, TaskListResponse, TaskResponse, TaskUpdate


def _normalize_datetime(value: datetime | None) -> datetime | None:
    """Convert timezone-aware datetimes to UTC-naive values for consistent API serialization."""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc)
    return value.replace(tzinfo=None)


def _utc_now() -> datetime:
    """Return a UTC timestamp rounded to millisecond precision without timezone offset."""
    now = datetime.now(timezone.utc)
    return _normalize_datetime(now.replace(microsecond=(now.microsecond // 1000) * 1000))


def _get_tasks_collection():
    tasks_collection = get_database()["tasks"]
    tasks_collection.create_index("user_id")
    return tasks_collection


def _serialize_task(task_document: dict) -> TaskResponse:
    return TaskResponse(
        id=str(task_document["_id"]),
        user_id=str(task_document["user_id"]),
        title=task_document["title"],
        description=task_document["description"],
        status=task_document["status"],
        priority=task_document["priority"],
        due_date=_normalize_datetime(task_document.get("due_date")),
        created_at=_normalize_datetime(task_document["created_at"]),
        updated_at=_normalize_datetime(task_document["updated_at"]),
    )


def create_task(user_id: str, task_data: TaskCreate) -> TaskResponse:
    """Create a task for the authenticated user."""
    tasks_collection = _get_tasks_collection()
    now = _utc_now()

    task_document = {
        "user_id": ObjectId(user_id),
        "title": task_data.title.strip(),
        "description": task_data.description.strip(),
        "status": task_data.status,
        "priority": task_data.priority,
        "due_date": _normalize_datetime(task_data.due_date),
        "created_at": now,
        "updated_at": now,
    }

    inserted = tasks_collection.insert_one(task_document)
    task_document["_id"] = inserted.inserted_id
    return _serialize_task(task_document)


def get_user_tasks(user_id: str) -> list[TaskResponse]:
    """Return all tasks belonging to the authenticated user."""
    tasks_collection = _get_tasks_collection()
    task_documents = tasks_collection.find({"user_id": ObjectId(user_id)})
    return [_serialize_task(task) for task in task_documents]


def get_task_analytics(user_id: str) -> TaskAnalyticsResponse:
    """Return MongoDB-aggregated analytics for the authenticated user's tasks."""
    tasks_collection = _get_tasks_collection()
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {
            "$group": {
                "_id": None,
                "total_tasks": {"$sum": 1},
                "completed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                "pending_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
                "in_progress_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}},
                "low_priority_tasks": {"$sum": {"$cond": [{"$eq": ["$priority", "low"]}, 1, 0]}},
                "medium_priority_tasks": {"$sum": {"$cond": [{"$eq": ["$priority", "medium"]}, 1, 0]}},
                "high_priority_tasks": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
            }
        },
    ]

    result = next(tasks_collection.aggregate(pipeline), None)
    if result is None:
        return TaskAnalyticsResponse(
            total_tasks=0,
            completed_tasks=0,
            pending_tasks=0,
            in_progress_tasks=0,
            low_priority_tasks=0,
            medium_priority_tasks=0,
            high_priority_tasks=0,
            completion_rate=0.0,
        )

    total_tasks = int(result.get("total_tasks", 0))
    completed_tasks = int(result.get("completed_tasks", 0))
    completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0.0

    return TaskAnalyticsResponse(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=int(result.get("pending_tasks", 0)),
        in_progress_tasks=int(result.get("in_progress_tasks", 0)),
        low_priority_tasks=int(result.get("low_priority_tasks", 0)),
        medium_priority_tasks=int(result.get("medium_priority_tasks", 0)),
        high_priority_tasks=int(result.get("high_priority_tasks", 0)),
        completion_rate=completion_rate,
    )


def get_user_tasks_paginated(
    user_id: str,
    *,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
) -> TaskListResponse:
    """Return filtered, searchable, paginated tasks for the authenticated user."""
    if status is not None and status not in {"pending", "in_progress", "completed"}:
        raise ValueError("Invalid status")
    if priority is not None and priority not in {"low", "medium", "high"}:
        raise ValueError("Invalid priority")
    if page < 1:
        raise ValueError("Page must be at least 1")
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if limit > 100:
        raise ValueError("Limit cannot exceed 100")

    tasks_collection = _get_tasks_collection()
    filter_query: dict = {"user_id": ObjectId(user_id)}

    if status is not None:
        filter_query["status"] = status
    if priority is not None:
        filter_query["priority"] = priority

    search_term = (search or "").strip()
    if search_term:
        safe_pattern = re.escape(search_term)
        filter_query["$or"] = [
            {"title": {"$regex": safe_pattern, "$options": "i"}},
            {"description": {"$regex": safe_pattern, "$options": "i"}},
        ]

    total = tasks_collection.count_documents(filter_query)
    pages = math.ceil(total / limit) if total else 0
    skip = (page - 1) * limit
    task_documents = (
        tasks_collection.find(filter_query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return TaskListResponse(
        items=[_serialize_task(task) for task in task_documents],
        page=page,
        limit=limit,
        total=total,
        pages=pages,
    )


def get_task(user_id: str, task_id: str) -> TaskResponse:
    """Return one task only if it belongs to the authenticated user."""
    tasks_collection = _get_tasks_collection()

    try:
        object_id = ObjectId(task_id)
    except (InvalidId, ValueError) as exc:
        raise ValueError("Invalid task ID") from exc

    task_document = tasks_collection.find_one({"_id": object_id, "user_id": ObjectId(user_id)})
    if task_document is None:
        raise ValueError("Task not found")

    return _serialize_task(task_document)


def update_task(user_id: str, task_id: str, task_data: TaskUpdate) -> TaskResponse:
    """Update an existing task only if it belongs to the authenticated user."""
    tasks_collection = _get_tasks_collection()

    try:
        object_id = ObjectId(task_id)
    except (InvalidId, ValueError) as exc:
        raise ValueError("Invalid task ID") from exc

    existing_task = tasks_collection.find_one({"_id": object_id, "user_id": ObjectId(user_id)})
    if existing_task is None:
        raise ValueError("Task not found")

    updates = task_data.model_dump(exclude_unset=True)
    if not updates:
        return _serialize_task(existing_task)

    timestamp_now = _utc_now()
    updates["updated_at"] = timestamp_now
    updated_task = tasks_collection.find_one_and_update(
        {"_id": object_id, "user_id": ObjectId(user_id)},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )

    if updated_task is None:
        raise ValueError("Task not found")

    updated_task["created_at"] = _normalize_datetime(existing_task["created_at"])
    updated_task["updated_at"] = timestamp_now
    return _serialize_task(updated_task)


def delete_task(user_id: str, task_id: str) -> None:
    """Delete an existing task only if it belongs to the authenticated user."""
    tasks_collection = _get_tasks_collection()

    try:
        object_id = ObjectId(task_id)
    except (InvalidId, ValueError) as exc:
        raise ValueError("Invalid task ID") from exc

    deleted_task = tasks_collection.find_one_and_delete({"_id": object_id, "user_id": ObjectId(user_id)})
    if deleted_task is None:
        raise ValueError("Task not found")
