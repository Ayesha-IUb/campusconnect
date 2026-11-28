"""Authenticated profile and personal session endpoints."""
from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_current_user
from app.users.schemas import PasswordChange, ProfileUpdate
from app.auth import service as auth_service
from app.users import service as user_service
from app.core.models import CurrentUser

router = APIRouter(tags=["Users"])


@router.get("/api/me")
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


@router.patch("/api/me")
def update_me(payload: ProfileUpdate, request: Request,
              current_user: CurrentUser = Depends(get_current_user)):
    return user_service.update_profile(current_user["id"], payload.full_name, request)


@router.post("/api/me/password")
def change_password(payload: PasswordChange, request: Request,
                    current_user: CurrentUser = Depends(get_current_user)):
    auth_service.change_password(
        current_user["id"], current_user["email"],
        payload.current_password, payload.new_password, request,
    )
    return {"message": "Password changed. Please sign in again."}


@router.get("/api/auth/sessions")
def sessions(current_user: CurrentUser = Depends(get_current_user)):
    return auth_service.list_sessions(current_user["id"])


@router.delete("/api/auth/sessions/{session_id}")
def revoke_session(session_id: str, request: Request,
                   current_user: CurrentUser = Depends(get_current_user)):
    auth_service.revoke_session(current_user["id"], session_id, request)
    return {"message": "Session revoked."}


@router.post("/api/auth/sessions/revoke-others")
def revoke_other_sessions(request: Request,
                          current_user: CurrentUser = Depends(get_current_user)):
    count = auth_service.revoke_others(
        current_user["id"], current_user.get("session_id"), request
    )
    return {"revoked": count}


@router.post("/api/auth/sessions/revoke-all")
def revoke_all_sessions(request: Request,
                        current_user: CurrentUser = Depends(get_current_user)):
    count = auth_service.revoke_all(current_user["id"], request)
    return {"revoked": count}
