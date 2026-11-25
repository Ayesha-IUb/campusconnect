"""Group ownership and fine-grained shared request permissions."""
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException
from database import execute_query, get_database
from models import CurrentUser
from services.activity_service import record_activity


def _db():
    return get_database()


def _group(group_id: str) -> dict[str, Any]:
    result = execute_query(_db().table("groups").select("*").eq("id", group_id).limit(1))
    if not result.data:
        raise HTTPException(status_code=404, detail="Group not found.")
    return result.data[0]


def _member(group_id: str, user_id: str) -> dict[str, Any] | None:
    result = execute_query(_db().table("group_members").select("*")
        .eq("group_id", group_id).eq("user_id", user_id).limit(1))
    return result.data[0] if result.data else None


def require_group_permission(group_id: str, user: CurrentUser, permission: str) -> dict[str, Any]:
    group = _group(group_id)
    if group["owner_id"] == user["id"] or user["role"] == "admin":
        return group
    member = _member(group_id, user["id"])
    if not member:
        raise HTTPException(status_code=404, detail="Group not found.")
    if not member.get(permission, False):
        raise HTTPException(status_code=403, detail="Group permission denied.")
    return group


def list_groups(user: CurrentUser) -> list[dict[str, Any]]:
    db = _db()
    owned = execute_query(db.table("groups").select("*").eq("owner_id", user["id"])).data or []
    membership = execute_query(db.table("group_members").select("group_id").eq("user_id", user["id"])).data or []
    ids = [row["group_id"] for row in membership]
    shared = execute_query(db.table("groups").select("*").in_("id", ids)).data or [] if ids else []
    unique = {row["id"]: row for row in owned + shared}
    return sorted(unique.values(), key=lambda row: row.get("created_at", ""), reverse=True)


def create_group(payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    result = execute_query(_db().table("groups").insert({
        "name": payload["name"].strip(), "description": payload.get("description", "").strip(),
        "owner_id": user["id"],
    }).select("*"))
    group = result.data[0]
    record_activity(user["id"], "group_created", "group", group["id"], request)
    return group


def update_group(group_id: str, payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the group owner can rename a group.")
    result = execute_query(_db().table("groups").update({
        "name": payload["name"].strip(), "description": payload.get("description", "").strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", group_id).select("*"))
    record_activity(user["id"], "group_updated", "group", group_id, request)
    return result.data[0]


def add_member(group_id: str, payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage members.")
    profiles = execute_query(_db().table("profiles").select("id,email")
        .eq("email", payload["email"].strip().lower()).limit(1))
    if not profiles.data:
        raise HTTPException(status_code=404, detail="Registered user not found.")
    member_id = profiles.data[0]["id"]
    if member_id == group["owner_id"]:
        raise HTTPException(status_code=400, detail="The owner is already a group member.")
    permissions = {key: bool(payload.get(key, False)) for key in (
        "can_create_requests", "can_edit_requests", "can_assign_requests",
    )}
    old = _member(group_id, member_id)
    if old:
        result = execute_query(_db().table("group_members").update(permissions)
            .eq("id", old["id"]).select("*"))
    else:
        result = execute_query(_db().table("group_members").insert({
            "group_id": group_id, "user_id": member_id, **permissions,
        }).select("*"))
    record_activity(user["id"], "group_member_added_or_updated", "group", group_id, request,
                    {"member_id": member_id})
    return result.data[0]


def remove_member(group_id: str, member_id: str, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only the owner can manage members.")
    result = execute_query(_db().table("group_members").delete()
        .eq("group_id", group_id).eq("user_id", member_id).select("id"))
    if not result.data:
        raise HTTPException(status_code=404, detail="Group member not found.")
    record_activity(user["id"], "group_member_removed", "group", group_id, request,
                    {"member_id": member_id})


def list_members(group_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    group = _group(group_id)
    if group["owner_id"] != user["id"] and user["role"] != "admin" and not _member(group_id, user["id"]):
        raise HTTPException(status_code=404, detail="Group not found.")
    result = execute_query(_db().table("group_members").select(
        "id,user_id,can_create_requests,can_edit_requests,can_assign_requests,created_at"
    ).eq("group_id", group_id))
    return result.data or []


def delete_group(group_id: str, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete a group.")
    execute_query(_db().table("groups").delete().eq("id", group_id))
    record_activity(user["id"], "group_deleted", "group", group_id, request)


def create_group_request(group_id: str, payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    require_group_permission(group_id, user, "can_create_requests")
    values = {key: payload[key] for key in ("title", "description", "category") if key in payload}
    values.update({"group_id": group_id, "user_id": user["id"], "status": "Pending"})
    assigned = payload.get("assigned_to")
    if assigned:
        require_group_permission(group_id, user, "can_assign_requests")
        if assigned != _group(group_id)["owner_id"] and not _member(group_id, assigned):
            raise HTTPException(status_code=422, detail="Assignee must be a group member.")
        values["assigned_to"] = assigned
    result = execute_query(_db().table("service_requests").insert(values).select("*"))
    record_activity(user["id"], "group_request_created", "request", result.data[0]["id"], request,
                    {"group_id": group_id})
    return result.data[0]


def list_group_requests(group_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    group = _group(group_id)
    if group["owner_id"] != user["id"] and user["role"] != "admin" and not _member(group_id, user["id"]):
        raise HTTPException(status_code=404, detail="Group not found.")
    result = execute_query(_db().table("service_requests").select("*")
        .eq("group_id", group_id).order("created_at", desc=True))
    return result.data or []


def update_group_request(group_id: str, request_id: int, payload: dict[str, Any],
                         user: CurrentUser, request) -> dict[str, Any]:
    group = require_group_permission(group_id, user, "can_edit_requests")
    existing = execute_query(_db().table("service_requests").select("*")
        .eq("id", request_id).eq("group_id", group_id).limit(1))
    if not existing.data:
        raise HTTPException(status_code=404, detail="Group request not found.")
    values = {key: value for key, value in payload.items() if value is not None}
    if "assigned_to" in values:
        require_group_permission(group_id, user, "can_assign_requests")
        assignee = values["assigned_to"]
        if assignee and assignee != group["owner_id"] and not _member(group_id, assignee):
            raise HTTPException(status_code=422, detail="Assignee must be a group member.")
    if not values:
        return existing.data[0]
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = execute_query(_db().table("service_requests").update(values)
        .eq("id", request_id).eq("group_id", group_id).select("*"))
    record_activity(user["id"], "group_request_updated", "request", request_id, request,
                    {"group_id": group_id})
    return result.data[0]


def delete_group_request(group_id: str, request_id: int, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete shared requests.")
    result = execute_query(_db().table("service_requests").delete()
        .eq("id", request_id).eq("group_id", group_id).select("id"))
    if not result.data:
        raise HTTPException(status_code=404, detail="Group request not found.")
    record_activity(user["id"], "group_request_deleted", "request", request_id, request,
                    {"group_id": group_id})
