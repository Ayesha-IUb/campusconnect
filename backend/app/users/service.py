"""Business logic for user profile management."""
from datetime import datetime, timezone

from fastapi import HTTPException

from app.users import repository as users_repo
from app.activity.service import record_activity


def update_profile(user_id: str, full_name: str, request) -> dict:
    result = users_repo.update_profile(
        user_id, full_name.strip(), datetime.now(timezone.utc).isoformat()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")

    record_activity(user_id, "profile_updated", "user", user_id, request)
    return result.data[0]
