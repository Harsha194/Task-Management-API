from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a user account after validating input and hashing the password.",
)
def register_user_route(user: UserCreate) -> UserResponse:
    try:
        return register_user(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user and return a JWT token",
    description="Validate the provided email and password, then issue a bearer token.",
)
def login_user_route(payload: LoginRequest) -> TokenResponse:
    try:
        return login_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's profile",
    description="Return the currently authenticated user's public profile information.",
)
def get_current_user_route(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
