from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings


client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Create and reuse a single MongoDB client instance."""
    global client

    if client is None:
        client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)

    return client


def get_database() -> Database[Any]:
    """Return the configured database object."""
    mongo_client = get_mongo_client()
    return mongo_client[settings.database_name]


def check_database_connection() -> dict[str, str]:
    """Ping MongoDB and report whether the database is reachable."""
    try:
        database = get_database()
        database.client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:  # pragma: no cover - depends on external DB availability
        return {
            "status": "error",
            "database": "unavailable",
            "detail": f"MongoDB connection failed: {exc}",
        }
