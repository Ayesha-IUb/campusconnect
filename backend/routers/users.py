"""Authenticated user endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_current_user
from models import CurrentUser

router = APIRouter(tags=["Users"])


@router.get("/api/me")
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
