"""Service request CRUD API routes."""

from fastapi import APIRouter, Depends, status

from database import get_database
from dependencies import get_current_user
from schemas import (
    DeleteResponse,
    RequestCreate,
    RequestUpdate,
    ServiceRequestResponse,
)
from services import request_service

router = APIRouter(prefix="/api/requests", tags=["Service Requests"])


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    request: RequestCreate,
    current_user: dict[str, str] = Depends(get_current_user),
):
    return request_service.create_request(get_database(), request, current_user)


@router.get("", response_model=list[ServiceRequestResponse])
def get_all_requests(
    current_user: dict[str, str] = Depends(get_current_user),
):
    return request_service.list_requests(get_database(), current_user)


@router.get("/{request_id}", response_model=ServiceRequestResponse)
def get_request(
    request_id: int,
    current_user: dict[str, str] = Depends(get_current_user),
):
    return request_service.get_request_by_id(
        get_database(), request_id, current_user
    )


@router.put("/{request_id}", response_model=ServiceRequestResponse)
def update_request(
    request_id: int,
    request: RequestUpdate,
    current_user: dict[str, str] = Depends(get_current_user),
):
    return request_service.update_request(
        get_database(), request_id, request, current_user
    )


@router.delete("/{request_id}", response_model=DeleteResponse)
def delete_request(
    request_id: int,
    current_user: dict[str, str] = Depends(get_current_user),
):
    return request_service.delete_request(
        get_database(), request_id, current_user
    )
