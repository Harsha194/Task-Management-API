from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_user_success() -> None:
    email = f"login.{uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Harsha Login",
        "email": email,
        "password": "StrongPassword123",
    }
    client.post("/auth/register", json=payload)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": payload["password"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert isinstance(data["access_token"], str)


def test_login_user_invalid_password() -> None:
    email = f"badpass.{uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Harsha Login",
        "email": email,
        "password": "StrongPassword123",
    }
    client.post("/auth/register", json=payload)

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_user_unknown_email() -> None:
    response = client.post(
        "/auth/login",
        json={"email": "missing.user@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_get_current_user_requires_valid_token() -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_get_current_user_without_token() -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_register_user_success() -> None:
    email = f"harsha.{uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Harsha Test",
        "email": email,
        "password": "StrongPassword123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "password" not in data
    assert "password_hash" not in data
    assert "id" in data


def test_register_user_invalid_email() -> None:
    payload = {
        "name": "Harsha",
        "email": "not-an-email",
        "password": "StrongPassword123",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_user_short_password() -> None:
    payload = {
        "name": "Harsha",
        "email": f"harsha2.{uuid4().hex[:8]}@example.com",
        "password": "short",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_register_user_duplicate_email() -> None:
    unique_email = f"harsha.duplicate.{uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Harsha Test",
        "email": unique_email,
        "password": "StrongPassword123",
    }

    first_response = client.post("/auth/register", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/auth/register", json=payload)
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"
