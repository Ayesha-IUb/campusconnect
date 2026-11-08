"""Authentication-related API routes."""

from fastapi import APIRouter, Depends

from dependencies import get_current_user
from schemas import ProfileResponse

router = APIRouter(tags=["Authentication"])


@router.get("/api/me", response_model=ProfileResponse)
def get_me(current_user: dict[str, str] = Depends(get_current_user)):
    return current_user
