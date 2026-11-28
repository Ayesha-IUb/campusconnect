"""Reusable authorization policy functions for CampusConnect."""
from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user
from app.core.models import CurrentUser

ROLE_STUDENT = "student"
ROLE_STAFF = "staff"
ROLE_ADMIN = "admin"
ALL_ROLES = {ROLE_STUDENT, ROLE_STAFF, ROLE_ADMIN}


def is_admin(user: CurrentUser) -> bool:
    return user.get("role") == ROLE_ADMIN


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user


def assert_can_create_request(user: CurrentUser) -> None:
    if user.get("role") not in {ROLE_STUDENT, ROLE_ADMIN}:
        raise HTTPException(status_code=403, detail="Only students and admins can create requests.")


def assert_can_update_request(user: CurrentUser, existing: dict, payload: dict) -> None:
    role = user.get("role")
    if role == ROLE_ADMIN:
        return
    if role == ROLE_STUDENT:
        if existing.get("user_id") != user.get("id") or existing.get("status") != "Pending":
            raise HTTPException(status_code=403, detail="You can edit only your own pending requests.")
        if payload.get("status", existing.get("status")) != existing.get("status"):
            raise HTTPException(status_code=403, detail="Students cannot change request status.")
        return
    if role == ROLE_STAFF:
        editable_fields = ("title", "description", "category")
        if any(payload.get(key) != existing.get(key) for key in editable_fields):
            raise HTTPException(status_code=403, detail="Staff can update request status only.")
        return
    raise HTTPException(status_code=403, detail="You do not have permission to update requests.")


def assert_can_delete_request(user: CurrentUser, existing: dict) -> None:
    role = user.get("role")
    if role == ROLE_ADMIN:
        return
    if role == ROLE_STUDENT and existing.get("user_id") == user.get("id") and existing.get("status") == "Pending":
        return
    if role == ROLE_STAFF:
        raise HTTPException(status_code=403, detail="Staff members cannot delete requests.")
    raise HTTPException(status_code=403, detail="You can delete only your own pending requests.")
