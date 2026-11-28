"""Database operations for authentication dependencies."""
from app.core.database import execute_query, get_database


def get_user_profile(user_id: str):
    return execute_query(
        get_database().table("profiles")
        .select("id,email,full_name,role,is_banned")
        .eq("id", user_id).limit(1)
    )


def get_active_session(user_id: str, access_hash: str):
    return execute_query(
        get_database().table("app_sessions").select("id")
        .eq("user_id", user_id)
        .eq("access_token_hash", access_hash)
        .is_("revoked_at", "null").limit(1)
    )
