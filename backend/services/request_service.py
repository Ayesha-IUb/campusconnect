"""Request CRUD operations and role-based business rules."""

from typing import Any

from fastapi import HTTPException, status

from database import execute_query
from schemas import RequestCreate, RequestUpdate


def create_request(db: Any, request: RequestCreate, current_user: dict[str, str]):
    if current_user["role"] not in {"student", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and admins can create requests.",
        )

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


def list_requests(db: Any, current_user: dict[str, str]):
    query = db.table("service_requests").select("*")
    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.order("created_at", desc=True))
    return result.data or []


def get_request_by_id(db: Any, request_id: int, current_user: dict[str, str]):
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
    db: Any,
    request_id: int,
    request: RequestUpdate,
    current_user: dict[str, str],
):
    existing = get_request_by_id(db, request_id, current_user)
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


def delete_request(db: Any, request_id: int, current_user: dict[str, str]):
    role = current_user["role"]
    if role == "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members cannot delete requests.",
        )

    query = db.table("service_requests").delete().eq("id", request_id)
    if role == "student":
        query = query.eq("user_id", current_user["id"]).eq("status", "Pending")
    elif role != "admin":
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
