"""Database operations for audit and security events."""
from typing import Any
from app.core.database import get_database


def insert_event(table: str, payload: dict[str, Any]) -> None:
    get_database().table(table).insert(payload).execute()
