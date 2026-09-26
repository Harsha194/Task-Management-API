from fastapi import APIRouter, HTTPException, status

from app.database import check_database_connection

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check", description="Returns the API health status.")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get(
    "/health/db",
    summary="Database health check",
    description="Checks whether MongoDB is reachable.",
)
def database_health_check() -> dict[str, str]:
    result = check_database_connection()

    if result["database"] == "connected":
        return result

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=result["detail"],
    )
