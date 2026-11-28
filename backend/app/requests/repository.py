"""Persistence operations for service requests."""
from typing import Any

from app.core.database import execute_query, get_database


class RequestRepository:
    def create(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(
            get_database().table("service_requests").insert(payload).select("*")
        )
        return result.data[0] if result.data else None

    def list_for_user(self, user_id: str | None = None) -> list[dict[str, Any]]:
        query = get_database().table("service_requests").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        result = execute_query(query.order("created_at", desc=True))
        return result.data or []

    def get_by_id(
        self, request_id: int, user_id: str | None = None
    ) -> dict[str, Any] | None:
        query = get_database().table("service_requests").select("*").eq("id", request_id)
        if user_id:
            query = query.eq("user_id", user_id)
        result = execute_query(query.limit(1))
        return result.data[0] if result.data else None

    def update(self, request_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(
            get_database().table("service_requests")
            .update(payload)
            .eq("id", request_id)
            .select("*")
        )
        return result.data[0] if result.data else None

    def delete(self, request_id: int) -> bool:
        result = execute_query(
            get_database().table("service_requests")
            .delete()
            .eq("id", request_id)
            .select("id")
        )
        return bool(result.data)


request_repository = RequestRepository()
