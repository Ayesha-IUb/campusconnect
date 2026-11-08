"""Public health-check route."""

from fastapi import APIRouter

from database import supabase

router = APIRouter(tags=["Health"])


@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "database_configured": supabase is not None,
    }
