"""Request business rules and RBAC. Database persistence is delegated to the repository."""
from typing import Any
from fastapi import HTTPException, Request

from models import CurrentUser
from schemas import RequestCreate, RequestUpdate
from rbac import assert_can_create_request, assert_can_delete_request, assert_can_update_request
from repositories.request_repository import request_repository
from services.activity_service import record_activity


def create_request(request_data: RequestCreate, current_user: CurrentUser,
                   request: Request | None = None) -> dict[str, Any]:
    assert_can_create_request(current_user)
    payload = request_data.model_dump()
    payload.update({"user_id": current_user["id"], "status": "Pending"})
    saved = request_repository.create(payload)
    if not saved:
        raise HTTPException(status_code=500, detail="Could not create service request.")
    record_activity(current_user["id"], "request_created", "request", saved.get("id"), request)
    return saved


def list_requests(current_user: CurrentUser) -> list[dict[str, Any]]:
    owner_id = current_user["id"] if current_user["role"] == "student" else None
    return request_repository.list_for_user(owner_id)


def get_request(request_id: int, current_user: CurrentUser) -> dict[str, Any]:
    owner_id = current_user["id"] if current_user["role"] == "student" else None
    saved = request_repository.get_by_id(request_id, owner_id)
    if not saved:
        raise HTTPException(status_code=404, detail="Service request not found.")
    return saved


def update_request(request_id: int, request_data: RequestUpdate,
                   current_user: CurrentUser, request: Request | None = None) -> dict[str, Any]:
    owner_id = current_user["id"] if current_user["role"] == "student" else None
    existing = request_repository.get_by_id(request_id, owner_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Service request not found.")
    payload = request_data.model_dump()
    assert_can_update_request(current_user, existing, payload)
    updated = request_repository.update(request_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Service request not found.")
    record_activity(current_user["id"], "request_updated", "request", request_id, request,
                    {"status": updated.get("status")})
    return updated


def delete_request(request_id: int, current_user: CurrentUser,
                   request: Request | None = None) -> dict[str, Any]:
    owner_id = current_user["id"] if current_user["role"] == "student" else None
    existing = request_repository.get_by_id(request_id, owner_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Service request not found.")
    assert_can_delete_request(current_user, existing)
    if not request_repository.delete(request_id):
        raise HTTPException(status_code=404, detail="Service request not found.")
    record_activity(current_user["id"], "request_deleted", "request", request_id, request)
    return {"message": "Service request deleted successfully.", "id": request_id}
