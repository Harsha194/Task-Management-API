from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.tasks import router as tasks_router

app = FastAPI(
    title="Task Management API",
    description="A beginner-friendly task management backend built with FastAPI and MongoDB.",
    version="0.1.0",
)


@app.get("/", summary="Root endpoint", description="Basic application welcome endpoint.")
def read_root() -> dict[str, str]:
    return {"message": "Task Management API is running"}


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
