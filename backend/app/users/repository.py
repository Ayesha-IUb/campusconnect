"""Database operations for user profiles."""
from app.core.database import execute_query, get_database


def update_profile(user_id: str, full_name: str, updated_at: str):
    return execute_query(
        get_database().table("profiles").update({
            "full_name": full_name,
            "updated_at": updated_at,
        }).eq("id", user_id).select("id,email,full_name,role")
    )
