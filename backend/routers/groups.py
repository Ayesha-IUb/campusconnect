"""Shared groups and group-request endpoints."""
from fastapi import APIRouter, Depends, Request, status

from dependencies import get_current_user
from models import CurrentUser
from schemas import GroupCreate, GroupMemberInput, GroupRequestCreate, GroupRequestUpdate, GroupUpdate
from services import group_service

router = APIRouter(prefix="/api/groups", tags=["Groups"])


@router.get("")
def list_groups(user: CurrentUser = Depends(get_current_user)):
    return group_service.list_groups(user)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, request: Request,
                 user: CurrentUser = Depends(get_current_user)):
    return group_service.create_group(payload.model_dump(), user, request)


@router.get("/{group_id}")
def group_members(group_id: str, user: CurrentUser = Depends(get_current_user)):
    return {"group_id": group_id, "members": group_service.list_members(group_id, user)}


@router.patch("/{group_id}")
def update_group(group_id: str, payload: GroupUpdate, request: Request,
                 user: CurrentUser = Depends(get_current_user)):
    return group_service.update_group(group_id, payload.model_dump(), user, request)


@router.delete("/{group_id}")
def delete_group(group_id: str, request: Request,
                 user: CurrentUser = Depends(get_current_user)):
    group_service.delete_group(group_id, user, request)
    return {"message": "Group deleted."}


@router.post("/{group_id}/members")
def add_member(group_id: str, payload: GroupMemberInput, request: Request,
               user: CurrentUser = Depends(get_current_user)):
    return group_service.add_member(group_id, payload.model_dump(), user, request)


@router.delete("/{group_id}/members/{member_id}")
def remove_member(group_id: str, member_id: str, request: Request,
                  user: CurrentUser = Depends(get_current_user)):
    group_service.remove_member(group_id, member_id, user, request)
    return {"message": "Member removed."}


@router.get("/{group_id}/requests")
def list_group_requests(group_id: str, user: CurrentUser = Depends(get_current_user)):
    return group_service.list_group_requests(group_id, user)


@router.post("/{group_id}/requests", status_code=status.HTTP_201_CREATED)
def create_group_request(group_id: str, payload: GroupRequestCreate, request: Request,
                         user: CurrentUser = Depends(get_current_user)):
    return group_service.create_group_request(group_id, payload.model_dump(), user, request)


@router.patch("/{group_id}/requests/{request_id}")
def update_group_request(group_id: str, request_id: int, payload: GroupRequestUpdate,
                         request: Request, user: CurrentUser = Depends(get_current_user)):
    return group_service.update_group_request(
        group_id, request_id, payload.model_dump(exclude_unset=True), user, request
    )


@router.delete("/{group_id}/requests/{request_id}")
def delete_group_request(group_id: str, request_id: int, request: Request,
                         user: CurrentUser = Depends(get_current_user)):
    group_service.delete_group_request(group_id, request_id, user, request)
    return {"message": "Group request deleted."}
