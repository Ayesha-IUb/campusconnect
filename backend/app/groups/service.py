"""Group business rules, ownership and fine-grained permission checks."""
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException

from app.core.models import CurrentUser
from app.groups.repository import group_repository as repo
from app.activity.service import record_activity


def _group(group_id: str) -> dict[str, Any]:
    group = repo.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")
    return group


def _member(group_id: str, user_id: str) -> dict[str, Any] | None:
    return repo.get_member(group_id, user_id)


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
    return repo.list_groups_for_user(user["id"])


def create_group(payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    group = repo.create_group({
        "name": payload["name"].strip(),
        "description": payload.get("description", "").strip(),
        "owner_id": user["id"],
    })
    if not group:
        raise HTTPException(status_code=500, detail="Could not create group.")
    record_activity(user["id"], "group_created", "group", group["id"], request)
    return group


def update_group(group_id: str, payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the group owner can rename a group.")
    result = repo.update_group(group_id, {
        "name": payload["name"].strip(),
        "description": payload.get("description", "").strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    if not result:
        raise HTTPException(status_code=404, detail="Group not found.")
    record_activity(user["id"], "group_updated", "group", group_id, request)
    return result


def add_member(group_id: str, payload: dict[str, Any], user: CurrentUser, request) -> dict[str, Any]:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage members.")
    profile = repo.get_profile_by_email(payload["email"].strip().lower())
    if not profile:
        raise HTTPException(status_code=404, detail="Registered user not found.")
    member_id = profile["id"]
    if member_id == group["owner_id"]:
        raise HTTPException(status_code=400, detail="The owner is already a group member.")
    permissions = {key: bool(payload.get(key, False)) for key in (
        "can_create_requests", "can_edit_requests", "can_assign_requests",
    )}
    saved = repo.add_or_update_member(group_id, member_id, permissions)
    if not saved:
        raise HTTPException(status_code=500, detail="Could not save group member.")
    record_activity(user["id"], "group_member_added_or_updated", "group", group_id,
                    request, {"member_id": member_id})
    return saved


def remove_member(group_id: str, member_id: str, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can manage members.")
    if not repo.remove_member(group_id, member_id):
        raise HTTPException(status_code=404, detail="Group member not found.")
    record_activity(user["id"], "group_member_removed", "group", group_id, request,
                    {"member_id": member_id})


def list_members(group_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    group = _group(group_id)
    if group["owner_id"] != user["id"] and user["role"] != "admin" and not _member(group_id, user["id"]):
        raise HTTPException(status_code=404, detail="Group not found.")
    return repo.list_members(group_id)


def delete_group(group_id: str, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete a group.")
    if not repo.delete_group(group_id):
        raise HTTPException(status_code=404, detail="Group not found.")
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
    saved = repo.create_group_request(values)
    if not saved:
        raise HTTPException(status_code=500, detail="Could not create shared request.")
    record_activity(user["id"], "group_request_created", "request", saved["id"], request,
                    {"group_id": group_id})
    return saved


def list_group_requests(group_id: str, user: CurrentUser) -> list[dict[str, Any]]:
    group = _group(group_id)
    if group["owner_id"] != user["id"] and user["role"] != "admin" and not _member(group_id, user["id"]):
        raise HTTPException(status_code=404, detail="Group not found.")
    return repo.list_group_requests(group_id)


def update_group_request(group_id: str, request_id: int, payload: dict[str, Any],
                         user: CurrentUser, request) -> dict[str, Any]:
    group = _group(group_id)
    existing = repo.get_group_request(group_id, request_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Group request not found.")
    values = {key: value for key, value in payload.items() if value is not None}
    edit_fields = set(values) - {"assigned_to"}
    if edit_fields:
        require_group_permission(group_id, user, "can_edit_requests")
    if "assigned_to" in values:
        require_group_permission(group_id, user, "can_assign_requests")
        assignee = values["assigned_to"]
        if assignee and assignee != group["owner_id"] and not _member(group_id, assignee):
            raise HTTPException(status_code=422, detail="Assignee must be a group member.")
    if not values:
        return existing
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    updated = repo.update_group_request(group_id, request_id, values)
    if not updated:
        raise HTTPException(status_code=404, detail="Group request not found.")
    record_activity(user["id"], "group_request_updated", "request", request_id, request,
                    {"group_id": group_id})
    return updated


def delete_group_request(group_id: str, request_id: int, user: CurrentUser, request) -> None:
    group = _group(group_id)
    if group["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can delete shared requests.")
    if not repo.delete_group_request(group_id, request_id):
        raise HTTPException(status_code=404, detail="Group request not found.")
    record_activity(user["id"], "group_request_deleted", "request", request_id, request,
                    {"group_id": group_id})
