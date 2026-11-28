"""Database operations for authentication and session management."""
from app.core.database import execute_query, get_database


def count_failed_attempts(email, ip, cutoff):
    result = execute_query(
        get_database().table("login_attempts").select("id")
        .eq("email", email).eq("ip_address", ip)
        .eq("succeeded", False).gte("created_at", cutoff)
    )
    return len(result.data or [])


def insert_login_attempt(email, ip, succeeded):
    return execute_query(
        get_database().table("login_attempts").insert({
            "email": email, "ip_address": ip, "succeeded": succeeded,
        })
    )


def get_profile(user_id):
    return execute_query(
        get_database().table("profiles")
        .select("id,email,full_name,role,is_banned")
        .eq("id", user_id).limit(1)
    )


def create_session(payload):
    return execute_query(
        get_database().table("app_sessions").insert(payload).select("id")
    )


def clear_failed_attempts(email, ip):
    return execute_query(
        get_database().table("login_attempts").delete()
        .eq("email", email).eq("ip_address", ip).eq("succeeded", False)
    )


def get_session_by_refresh_hash(refresh_hash):
    return execute_query(
        get_database().table("app_sessions")
        .select("id,user_id,expires_at,revoked_at")
        .eq("refresh_token_hash", refresh_hash).limit(1)
    )


def get_session_owner_by_refresh_hash(refresh_hash):
    return execute_query(
        get_database().table("app_sessions").select("id,user_id")
        .eq("refresh_token_hash", refresh_hash).limit(1)
    )


def revoke_session_by_id(session_id, revoked_at):
    return execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": revoked_at,
        }).eq("id", session_id)
    )


def rotate_session(session_id, old_hash, values):
    return execute_query(
        get_database().table("app_sessions").update(values)
        .eq("id", session_id).eq("refresh_token_hash", old_hash)
        .select("id")
    )


def list_user_sessions(user_id):
    return execute_query(
        get_database().table("app_sessions")
        .select("id,device_name,ip_address,user_agent,created_at,last_seen_at,expires_at,revoked_at")
        .eq("user_id", user_id).order("created_at", desc=True)
    )


def revoke_one_session(user_id, session_id, revoked_at):
    return execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": revoked_at,
        }).eq("id", session_id).eq("user_id", user_id)
        .is_("revoked_at", "null").select("id")
    )


def revoke_other_sessions(user_id, current_session_id, revoked_at):
    query = get_database().table("app_sessions").update({
        "revoked_at": revoked_at,
    }).eq("user_id", user_id).is_("revoked_at", "null")
    if current_session_id:
        query = query.neq("id", current_session_id)
    return execute_query(query.select("id"))


def revoke_all_sessions(user_id, revoked_at):
    return execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": revoked_at,
        }).eq("user_id", user_id).is_("revoked_at", "null").select("id")
    )
