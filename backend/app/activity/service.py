"""Audit and security event writers."""
from typing import Any
from fastapi import Request
from app.activity import repository as activity_repo


def request_context(request: Request | None) -> tuple[str | None, str | None]:
    if request is None:
        return None, None
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
    return ip, request.headers.get("user-agent", "")[:500]


def _insert(table: str, payload: dict[str, Any]) -> None:
    try:
        activity_repo.insert_event(table, payload)
    except Exception as exc:
        print(f"{table} write failed:", type(exc).__name__)


def record_activity(actor_id: str | None, action: str, entity_type: str = "system",
                    entity_id: str | int | None = None, request: Request | None = None,
                    details: dict[str, Any] | None = None) -> None:
    ip, agent = request_context(request)
    _insert("activity_logs", {
        "actor_id": actor_id, "action": action, "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "ip_address": ip, "user_agent": agent, "details": details or {},
    })


def record_security_event(event_type: str, request: Request | None = None,
                          actor_id: str | None = None, email: str | None = None,
                          details: dict[str, Any] | None = None) -> None:
    ip, agent = request_context(request)
    _insert("security_events", {
        "actor_id": actor_id, "event_type": event_type, "email": email,
        "ip_address": ip, "user_agent": agent, "details": details or {},
    })
