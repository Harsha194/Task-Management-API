from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as http_status

from app.dependencies.auth import get_current_user
from app.schemas.task import TaskAnalyticsResponse, TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import (
    create_task,
    delete_task,
    get_task,
    get_task_analytics,
    get_user_tasks,
    get_user_tasks_paginated,
    update_task,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a task for the authenticated user",
)
def create_task_route(task_data: TaskCreate, current_user=Depends(get_current_user)) -> TaskResponse:
    return create_task(current_user.id, task_data)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks for the authenticated user with optional filtering and pagination",
)
def get_user_tasks_route(
    current_user=Depends(get_current_user),
    status: str | None = Query(default=None, description="Filter by task status: pending, in_progress, completed"),
    priority: str | None = Query(default=None, description="Filter by task priority: low, medium, high"),
    search: str | None = Query(default=None, description="Case-insensitive text search in title and description"),
    page: int = Query(default=1, description="Page number starting at 1"),
    limit: int = Query(default=10, description="Items per page (1-100)"),
) -> TaskListResponse:
    try:
        return get_user_tasks_paginated(
            current_user.id,
            status=status,
            priority=priority,
            search=search,
            page=page,
            limit=limit,
        )
    except ValueError as exc:
        detail = str(exc)
        if detail in {"Invalid status", "Invalid priority", "Page must be at least 1", "Limit must be at least 1", "Limit cannot exceed 100"}:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=detail) from exc
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=detail) from exc


@router.get(
    "/analytics",
    response_model=TaskAnalyticsResponse,
    summary="Get task analytics for the authenticated user",
)
def get_task_analytics_route(current_user=Depends(get_current_user)) -> TaskAnalyticsResponse:
    return get_task_analytics(current_user.id)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task for the authenticated user",
)
def get_task_route(task_id: str, current_user=Depends(get_current_user)) -> TaskResponse:
    try:
        return get_task(current_user.id, task_id)
    except ValueError as exc:
        if str(exc) == "Invalid task ID":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid task ID") from exc
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task for the authenticated user",
)
def update_task_route(task_id: str, task_data: TaskUpdate, current_user=Depends(get_current_user)) -> TaskResponse:
    try:
        return update_task(current_user.id, task_id, task_data)
    except ValueError as exc:
        if str(exc) == "Invalid task ID":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid task ID") from exc
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found") from exc


@router.delete(
    "/{task_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete a task for the authenticated user",
)
def delete_task_route(task_id: str, current_user=Depends(get_current_user)) -> Response:
    try:
        delete_task(current_user.id, task_id)
    except ValueError as exc:
        if str(exc) == "Invalid task ID":
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid task ID") from exc
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found") from exc

    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
