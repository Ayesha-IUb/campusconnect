"""Supabase persistence operations for group resources."""
from typing import Any

from app.core.database import execute_query, get_database


class GroupRepository:
    def get_group(self, group_id: str) -> dict[str, Any] | None:
        result = execute_query(get_database().table("groups").select("*").eq("id", group_id).limit(1))
        return result.data[0] if result.data else None

    def get_member(self, group_id: str, user_id: str) -> dict[str, Any] | None:
        result = execute_query(get_database().table("group_members").select("*")
            .eq("group_id", group_id).eq("user_id", user_id).limit(1))
        return result.data[0] if result.data else None

    def get_profile_by_email(self, email: str) -> dict[str, Any] | None:
        result = execute_query(get_database().table("profiles").select("id,email")
            .eq("email", email).limit(1))
        return result.data[0] if result.data else None

    def list_groups_for_user(self, user_id: str) -> list[dict[str, Any]]:
        db = get_database()
        owned = execute_query(db.table("groups").select("*").eq("owner_id", user_id)).data or []
        membership = execute_query(db.table("group_members").select("group_id").eq("user_id", user_id)).data or []
        ids = [row["group_id"] for row in membership]
        shared = execute_query(db.table("groups").select("*").in_("id", ids)).data or [] if ids else []
        unique = {row["id"]: row for row in owned + shared}
        return sorted(unique.values(), key=lambda row: row.get("created_at", ""), reverse=True)

    def create_group(self, values: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(get_database().table("groups").insert(values).select("*"))
        return result.data[0] if result.data else None

    def update_group(self, group_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(get_database().table("groups").update(values)
            .eq("id", group_id).select("*"))
        return result.data[0] if result.data else None

    def delete_group(self, group_id: str) -> bool:
        result = execute_query(get_database().table("groups").delete()
            .eq("id", group_id).select("id"))
        return bool(result.data)

    def add_or_update_member(self, group_id: str, user_id: str,
                             permissions: dict[str, bool]) -> dict[str, Any] | None:
        existing = self.get_member(group_id, user_id)
        if existing:
            result = execute_query(get_database().table("group_members").update(permissions)
                .eq("id", existing["id"]).select("*"))
        else:
            result = execute_query(get_database().table("group_members").insert({
                "group_id": group_id, "user_id": user_id, **permissions,
            }).select("*"))
        return result.data[0] if result.data else None

    def remove_member(self, group_id: str, user_id: str) -> bool:
        result = execute_query(get_database().table("group_members").delete()
            .eq("group_id", group_id).eq("user_id", user_id).select("id"))
        return bool(result.data)

    def list_members(self, group_id: str) -> list[dict[str, Any]]:
        result = execute_query(get_database().table("group_members").select(
            "id,user_id,can_create_requests,can_edit_requests,can_assign_requests,created_at"
        ).eq("group_id", group_id))
        return result.data or []

    def list_group_requests(self, group_id: str) -> list[dict[str, Any]]:
        result = execute_query(get_database().table("service_requests").select("*")
            .eq("group_id", group_id).order("created_at", desc=True))
        return result.data or []

    def get_group_request(self, group_id: str, request_id: int) -> dict[str, Any] | None:
        result = execute_query(get_database().table("service_requests").select("*")
            .eq("id", request_id).eq("group_id", group_id).limit(1))
        return result.data[0] if result.data else None

    def create_group_request(self, values: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(get_database().table("service_requests").insert(values).select("*"))
        return result.data[0] if result.data else None

    def update_group_request(self, group_id: str, request_id: int,
                             values: dict[str, Any]) -> dict[str, Any] | None:
        result = execute_query(get_database().table("service_requests").update(values)
            .eq("id", request_id).eq("group_id", group_id).select("*"))
        return result.data[0] if result.data else None

    def delete_group_request(self, group_id: str, request_id: int) -> bool:
        result = execute_query(get_database().table("service_requests").delete()
            .eq("id", request_id).eq("group_id", group_id).select("id"))
        return bool(result.data)


group_repository = GroupRepository()
