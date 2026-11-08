"""REST endpoints for service request CRUD operations."""

from typing import Any

from fastapi import APIRouter, Depends, status

from dependencies import get_current_user
from models import CurrentUser
from schemas import RequestCreate, RequestUpdate
from services import request_service

router = APIRouter(prefix="/api/requests", tags=["Service Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    request: RequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return request_service.create_request(request, current_user)


@router.get("")
def get_all_requests(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    return request_service.list_requests(current_user)


@router.get("/{request_id}")
def get_request(
    request_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return request_service.get_request(request_id, current_user)


@router.put("/{request_id}")
def update_request(
    request_id: int,
    request: RequestUpdate,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return request_service.update_request(request_id, request, current_user)


@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return request_service.delete_request(request_id, current_user)
