"""Business rules and Supabase operations for service requests."""
from typing import Any
from fastapi import HTTPException, status, Request

from database import execute_query, get_database
from models import CurrentUser
from schemas import RequestCreate, RequestUpdate
from rbac import assert_can_create_request, assert_can_delete_request, assert_can_update_request
from services.activity_service import record_activity


def create_request(request_data: RequestCreate, current_user: CurrentUser,
                   request: Request | None = None) -> dict[str, Any]:
    assert_can_create_request(current_user)
    payload = request_data.model_dump()
    payload["user_id"] = current_user["id"]
    payload["status"] = "Pending"
    result = execute_query(get_database().table("service_requests").insert(payload))
    if not result.data:
        raise HTTPException(status_code=500, detail="Could not create service request.")
    saved = result.data[0]
    record_activity(current_user["id"], "request_created", "request", saved.get("id"), request)
    return saved


def list_requests(current_user: CurrentUser) -> list[dict[str, Any]]:
    query = get_database().table("service_requests").select("*")
    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])
    result = execute_query(query.order("created_at", desc=True))
    return result.data or []


def get_request(request_id: int, current_user: CurrentUser) -> dict[str, Any]:
    query = get_database().table("service_requests").select("*").eq("id", request_id)
    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])
    result = execute_query(query.limit(1))
    if not result.data:
        raise HTTPException(status_code=404, detail="Service request not found.")
    return result.data[0]


def update_request(request_id: int, request_data: RequestUpdate,
                   current_user: CurrentUser, request: Request | None = None) -> dict[str, Any]:
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)
    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])
    result = execute_query(query.limit(1))
    if not result.data:
        raise HTTPException(status_code=404, detail="Service request not found.")
    existing = result.data[0]
    payload = request_data.model_dump()
    assert_can_update_request(current_user, existing, payload)
    updated = execute_query(
        db.table("service_requests").update(payload).eq("id", request_id).select("*")
    )
    if not updated.data:
        raise HTTPException(status_code=404, detail="Service request not found.")
    record_activity(current_user["id"], "request_updated", "request", request_id, request,
                    {"status": updated.data[0].get("status")})
    return updated.data[0]


def delete_request(request_id: int, current_user: CurrentUser,
                   request: Request | None = None) -> dict[str, Any]:
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)
    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])
    existing = execute_query(query.limit(1))
    if not existing.data:
        raise HTTPException(status_code=404, detail="Service request not found.")
    assert_can_delete_request(current_user, existing.data[0])
    result = execute_query(db.table("service_requests").delete().eq("id", request_id).select("id"))
    if not result.data:
        raise HTTPException(status_code=404, detail="Service request not found.")
    record_activity(current_user["id"], "request_deleted", "request", request_id, request)
    return {"message": "Service request deleted successfully.", "id": request_id}
