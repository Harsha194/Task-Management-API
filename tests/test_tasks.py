from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_user(prefix: str = "task") -> tuple[str, str, str]:
    email = f"{prefix}.{uuid4().hex[:8]}@example.com"
    password = "StrongPassword123"
    payload = {"name": "Task User", "email": email, "password": password}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    return email, password, response.json()["id"]


def login_user(email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def create_task(token: str, payload: dict) -> dict:
    response = client.post("/tasks", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    return response.json()


def test_create_task_with_valid_jwt() -> None:
    email, password, _ = register_user("create")
    token = login_user(email, password)

    payload = {
        "title": "Learn FastAPI",
        "description": "Complete Task Management API",
        "status": "pending",
        "priority": "high",
        "due_date": None,
    }

    response = client.post("/tasks", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["status"] == payload["status"]
    assert data["priority"] == payload["priority"]
    assert data["due_date"] is None
    assert "user_id" in data
    assert data["user_id"]


def test_create_task_without_authentication() -> None:
    response = client.post(
        "/tasks",
        json={
            "title": "No auth",
            "description": "Does not matter",
            "status": "pending",
            "priority": "medium",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_user_tasks() -> None:
    email, password, _ = register_user("list")
    token = login_user(email, password)

    create_task(token, {"title": "Task 1", "description": "One", "status": "pending", "priority": "low"})
    create_task(token, {"title": "Task 2", "description": "Two", "status": "in_progress", "priority": "medium"})

    response = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] == 2
    assert {item["title"] for item in data["items"]} == {"Task 1", "Task 2"}


def test_get_user_tasks_default_pagination_and_metadata() -> None:
    email, password, _ = register_user("paginate")
    token = login_user(email, password)

    for index in range(15):
        create_task(token, {"title": f"Task {index}", "description": f"Description {index}", "status": "pending", "priority": "low"})

    response = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] == 15
    assert data["pages"] == 2
    assert len(data["items"]) == 10


def test_get_user_tasks_custom_page_and_limit() -> None:
    email, password, _ = register_user("custom-page")
    token = login_user(email, password)

    for index in range(25):
        create_task(token, {"title": f"Custom task {index}", "description": f"Meta {index}", "status": "completed", "priority": "medium"})

    response = client.get("/tasks?page=2&limit=5", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["limit"] == 5
    assert data["total"] == 25
    assert data["pages"] == 5
    assert len(data["items"]) == 5


def test_get_user_tasks_status_filter() -> None:
    email, password, _ = register_user("status-filter")
    token = login_user(email, password)

    create_task(token, {"title": "Pending task", "description": "pending", "status": "pending", "priority": "low"})
    create_task(token, {"title": "Completed task", "description": "done", "status": "completed", "priority": "high"})
    create_task(token, {"title": "In progress", "description": "active", "status": "in_progress", "priority": "medium"})

    response = client.get("/tasks?status=pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "pending"


def test_get_user_tasks_priority_filter() -> None:
    email, password, _ = register_user("priority-filter")
    token = login_user(email, password)

    create_task(token, {"title": "Low task", "description": "low", "status": "pending", "priority": "low"})
    create_task(token, {"title": "High task", "description": "high", "status": "pending", "priority": "high"})

    response = client.get("/tasks?priority=high", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["priority"] == "high"


def test_get_user_tasks_search_case_insensitive() -> None:
    email, password, _ = register_user("search")
    token = login_user(email, password)

    create_task(token, {"title": "FastAPI Task", "description": "Learn the framework", "status": "pending", "priority": "medium"})
    create_task(token, {"title": "Another task", "description": "No match here", "status": "pending", "priority": "low"})

    response = client.get("/tasks?search=FASTAPI", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "FastAPI Task"


def test_get_user_tasks_combined_filters_and_search() -> None:
    email, password, _ = register_user("combined")
    token = login_user(email, password)

    create_task(token, {"title": "API task", "description": "FastAPI work", "status": "pending", "priority": "high"})
    create_task(token, {"title": "API task 2", "description": "Other", "status": "completed", "priority": "high"})
    create_task(token, {"title": "Other task", "description": "FastAPI stuff", "status": "pending", "priority": "low"})

    response = client.get("/tasks?status=pending&priority=high&search=api&page=1&limit=10", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "API task"


def test_get_user_tasks_invalid_status_and_limit() -> None:
    email, password, _ = register_user("invalid-query")
    token = login_user(email, password)

    bad_status = client.get("/tasks?status=unknown", headers={"Authorization": f"Bearer {token}"})
    assert bad_status.status_code == 400
    assert bad_status.json()["detail"] == "Invalid status"

    bad_limit = client.get("/tasks?limit=0", headers={"Authorization": f"Bearer {token}"})
    assert bad_limit.status_code == 400
    assert bad_limit.json()["detail"] == "Limit must be at least 1"


def test_get_user_tasks_ownership_isolation_with_filters_and_search() -> None:
    email_a, password_a, _ = register_user("owner-a-search")
    token_a = login_user(email_a, password_a)
    email_b, password_b, _ = register_user("owner-b-search")
    token_b = login_user(email_b, password_b)

    create_task(token_a, {"title": "Alpha task", "description": "FastAPI project", "status": "pending", "priority": "high"})
    create_task(token_a, {"title": "Alpha second", "description": "More work", "status": "completed", "priority": "medium"})
    create_task(token_b, {"title": "Beta task", "description": "FastAPI secret", "status": "pending", "priority": "high"})

    response = client.get("/tasks?search=FastAPI", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    data = response.json()
    titles = {item["title"] for item in data["items"]}
    assert "Beta task" not in titles

    response_status = client.get("/tasks?status=pending", headers={"Authorization": f"Bearer {token_a}"})
    assert response_status.status_code == 200
    assert all(item["status"] == "pending" for item in response_status.json()["items"])

    response_page = client.get("/tasks?page=1&limit=1", headers={"Authorization": f"Bearer {token_a}"})
    assert response_page.status_code == 200
    assert response_page.json()["total"] == 2
    assert len(response_page.json()["items"]) == 1


def test_get_user_tasks_empty_result_set() -> None:
    email, password, _ = register_user("empty")
    token = login_user(email, password)

    response = client.get("/tasks?status=completed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


def test_get_user_task_analytics_requires_authentication() -> None:
    response = client.get("/tasks/analytics")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_user_task_analytics_returns_correct_counts() -> None:
    email, password, _ = register_user("analytics")
    token = login_user(email, password)

    create_task(token, {"title": "Task A", "description": "Pending low", "status": "pending", "priority": "low"})
    create_task(token, {"title": "Task B", "description": "Completed high", "status": "completed", "priority": "high"})
    create_task(token, {"title": "Task C", "description": "In progress medium", "status": "in_progress", "priority": "medium"})
    create_task(token, {"title": "Task D", "description": "Completed medium", "status": "completed", "priority": "medium"})
    create_task(token, {"title": "Task E", "description": "Pending low", "status": "pending", "priority": "low"})

    response = client.get("/tasks/analytics", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 5
    assert data["completed_tasks"] == 2
    assert data["pending_tasks"] == 2
    assert data["in_progress_tasks"] == 1
    assert data["low_priority_tasks"] == 2
    assert data["medium_priority_tasks"] == 2
    assert data["high_priority_tasks"] == 1
    assert data["completion_rate"] == 40.0


def test_get_user_task_analytics_empty_user() -> None:
    email, password, _ = register_user("empty-analytics")
    token = login_user(email, password)

    response = client.get("/tasks/analytics", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["completed_tasks"] == 0
    assert data["pending_tasks"] == 0
    assert data["in_progress_tasks"] == 0
    assert data["low_priority_tasks"] == 0
    assert data["medium_priority_tasks"] == 0
    assert data["high_priority_tasks"] == 0
    assert data["completion_rate"] == 0.0


def test_get_user_task_analytics_isolated_between_users() -> None:
    email_a, password_a, _ = register_user("analytics-a")
    token_a = login_user(email_a, password_a)
    email_b, password_b, _ = register_user("analytics-b")
    token_b = login_user(email_b, password_b)

    create_task(token_a, {"title": "A1", "description": "done", "status": "completed", "priority": "high"})
    create_task(token_a, {"title": "A2", "description": "done", "status": "completed", "priority": "medium"})
    create_task(token_a, {"title": "A3", "description": "pending", "status": "pending", "priority": "low"})

    create_task(token_b, {"title": "B1", "description": "done", "status": "completed", "priority": "low"})
    create_task(token_b, {"title": "B2", "description": "pending", "status": "pending", "priority": "medium"})
    create_task(token_b, {"title": "B3", "description": "pending", "status": "pending", "priority": "high"})

    response_a = client.get("/tasks/analytics", headers={"Authorization": f"Bearer {token_a}"})
    assert response_a.status_code == 200
    data_a = response_a.json()
    assert data_a["total_tasks"] == 3
    assert data_a["completed_tasks"] == 2
    assert data_a["pending_tasks"] == 1
    assert data_a["in_progress_tasks"] == 0
    assert data_a["high_priority_tasks"] == 1
    assert data_a["completion_rate"] == 66.67

    response_b = client.get("/tasks/analytics", headers={"Authorization": f"Bearer {token_b}"})
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert data_b["total_tasks"] == 3
    assert data_b["completed_tasks"] == 1
    assert data_b["pending_tasks"] == 2
    assert data_b["in_progress_tasks"] == 0
    assert data_b["medium_priority_tasks"] == 1
    assert data_b["high_priority_tasks"] == 1
    assert data_b["completion_rate"] == 33.33


def test_get_single_user_task() -> None:
    email, password, _ = register_user("single")
    token = login_user(email, password)
    created = create_task(token, {"title": "Single task", "description": "Details", "status": "pending", "priority": "high"})

    response = client.get(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["title"] == "Single task"


def test_update_user_task() -> None:
    email, password, _ = register_user("update")
    token = login_user(email, password)
    created = create_task(
        token,
        {
            "title": "Old title",
            "description": "Old description",
            "status": "pending",
            "priority": "low",
            "due_date": None,
        },
    )

    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "New title", "status": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["status"] == "completed"
    assert data["description"] == "Old description"
    assert data["created_at"] == created["created_at"]
    assert data["updated_at"] != created["updated_at"]


def test_delete_user_task() -> None:
    email, password, _ = register_user("delete")
    token = login_user(email, password)
    created = create_task(token, {"title": "Delete me", "description": "Later", "status": "pending", "priority": "medium"})

    response = client.delete(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert response.content == b""

    follow_up = client.get(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token}"})
    assert follow_up.status_code == 404
    assert follow_up.json()["detail"] == "Task not found"


def test_invalid_task_id() -> None:
    email, password, _ = register_user("invalid")
    token = login_user(email, password)

    response = client.get("/tasks/not-a-valid-id", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid task ID"


def test_nonexistent_task() -> None:
    email, password, _ = register_user("missing")
    token = login_user(email, password)
    task_id = "507f1f77bcf86cd799439011"

    response = client.get(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_user_cannot_access_another_users_task() -> None:
    email_a, password_a, _ = register_user("owner-a")
    token_a = login_user(email_a, password_a)
    task = create_task(token_a, {"title": "User A task", "description": "Private", "status": "pending", "priority": "high"})

    email_b, password_b, _ = register_user("owner-b")
    token_b = login_user(email_b, password_b)

    get_response = client.get(f"/tasks/{task['id']}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Task not found"

    put_response = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Hacked title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_response.status_code == 404
    assert put_response.json()["detail"] == "Task not found"

    delete_response = client.delete(f"/tasks/{task['id']}", headers={"Authorization": f"Bearer {token_b}"})
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Task not found"

    owner_get = client.get(f"/tasks/{task['id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert owner_get.status_code == 200
    assert owner_get.json()["title"] == "User A task"


def test_invalid_status_and_priority_validation() -> None:
    email, password, _ = register_user("validation")
    token = login_user(email, password)

    invalid_status = client.post(
        "/tasks",
        json={
            "title": "Invalid status",
            "description": "Does not matter",
            "status": "archived",
            "priority": "medium",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid_status.status_code == 422

    invalid_priority = client.post(
        "/tasks",
        json={
            "title": "Invalid priority",
            "description": "Does not matter",
            "status": "pending",
            "priority": "urgent",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid_priority.status_code == 422


def test_partial_update_allows_only_provided_fields() -> None:
    email, password, _ = register_user("partial")
    token = login_user(email, password)
    created = create_task(token, {"title": "Title A", "description": "Desc A", "status": "pending", "priority": "low"})

    response = client.put(
        f"/tasks/{created['id']}",
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Title A"
    assert data["description"] == "Updated description"
    assert data["status"] == "pending"
    assert data["priority"] == "low"


def test_created_at_stays_same_and_updated_at_changes() -> None:
    email, password, _ = register_user("timestamps")
    token = login_user(email, password)
    created = create_task(
        token,
        {
            "title": "Time task",
            "description": "Check timestamps",
            "status": "pending",
            "priority": "medium",
        },
    )

    created_at_initial = created["created_at"]
    updated_at_initial = created["updated_at"]

    updated = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Updated time task"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert updated.status_code == 200
    data = updated.json()
    assert data["created_at"] == created_at_initial
    assert data["updated_at"] != updated_at_initial
