"""Business rules and Supabase operations for service requests."""

from typing import Any

from fastapi import HTTPException, status

from database import execute_query, get_database
from models import CurrentUser
from schemas import RequestCreate, RequestUpdate


def create_request(request: RequestCreate, current_user: CurrentUser) -> dict[str, Any]:
    if current_user["role"] not in {"student", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and admins can create requests.",
        )

    db = get_database()
    payload = request.model_dump()
    payload["user_id"] = current_user["id"]
    payload["status"] = "Pending"

    result = execute_query(db.table("service_requests").insert(payload))
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create service request.",
        )
    return result.data[0]


def list_requests(current_user: CurrentUser) -> list[dict[str, Any]]:
    db = get_database()
    query = db.table("service_requests").select("*")

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.order("created_at", desc=True))
    return result.data or []


def get_request(request_id: int, current_user: CurrentUser) -> dict[str, Any]:
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.limit(1))
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )
    return result.data[0]


def update_request(
    request_id: int,
    request: RequestUpdate,
    current_user: CurrentUser,
) -> dict[str, Any]:
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.limit(1))
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    existing = result.data[0]
    payload = request.model_dump()
    role = current_user["role"]

    if role == "student":
        if existing.get("status") != "Pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can edit only your own pending requests.",
            )
        if payload["status"] != existing.get("status"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot change request status.",
            )

    elif role == "staff":
        unchanged_fields = (
            payload["title"] == existing.get("title")
            and payload["description"] == existing.get("description")
            and payload["category"] == existing.get("category")
        )
        if not unchanged_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff can update request status only.",
            )

    elif role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update requests.",
        )

    updated = execute_query(
        db.table("service_requests")
        .update(payload)
        .eq("id", request_id)
        .select("*")
    )
    if not updated.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )
    return updated.data[0]


def delete_request(request_id: int, current_user: CurrentUser) -> dict[str, Any]:
    if current_user["role"] == "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members cannot delete requests.",
        )

    db = get_database()
    query = db.table("service_requests").delete().eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"]).eq("status", "Pending")
    elif current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete requests.",
        )

    result = execute_query(query.select("id"))
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending service request not found.",
        )

    return {
        "message": "Service request deleted successfully.",
        "id": request_id,
    }
