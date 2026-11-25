"""Supabase authentication with rotated HttpOnly refresh-cookie sessions."""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException, Request

from database import SUPABASE_ANON_KEY, SUPABASE_URL, execute_query, get_database
from services.activity_service import record_activity, record_security_event

REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))


def _auth_request(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(status_code=503, detail="Supabase Auth is not configured on the backend.")
    try:
        response = httpx.post(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/{path}",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json=payload, timeout=15.0,
        )
        data = response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Authentication service is unavailable.") from exc
    if not response.is_success:
        message = data.get("msg") or data.get("message") or data.get("error_description")
        raise HTTPException(status_code=401, detail=message or "Authentication failed.")
    return data


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _context(request: Request) -> tuple[str, str]:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return ip[:100], request.headers.get("user-agent", "Unknown")[:500]


def register(email: str, password: str, full_name: str) -> dict[str, Any]:
    data = _auth_request("signup", {
        "email": email.strip().lower(), "password": password,
        "data": {"full_name": full_name.strip()},
    })
    if data.get("access_token"):
        return {"confirmation_required": False, "message": "Account created. You can now sign in."}
    return {"confirmation_required": True, "message": "Account created. Confirm your email before signing in."}


def login(email: str, password: str, request: Request) -> tuple[dict[str, Any], str]:
    email = email.strip().lower()
    ip, agent = _context(request)
    db = get_database()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    attempts = execute_query(
        db.table("login_attempts").select("id").eq("email", email).eq("ip_address", ip)
        .eq("succeeded", False).gte("created_at", cutoff)
    )
    if len(attempts.data or []) >= 5:
        record_security_event("login_locked", request, email=email)
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

    try:
        data = _auth_request("token?grant_type=password", {"email": email, "password": password})
    except HTTPException:
        execute_query(db.table("login_attempts").insert({
            "email": email, "ip_address": ip, "succeeded": False,
        }))
        record_security_event("login_failed", request, email=email)
        raise

    user_id = str((data.get("user") or {}).get("id") or "")
    profile = execute_query(
        db.table("profiles").select("id,email,full_name,role,is_banned")
        .eq("id", user_id).limit(1)
    )
    if not user_id or not profile.data:
        raise HTTPException(status_code=403, detail="User profile was not found.")
    user = profile.data[0]
    if user.get("is_banned"):
        record_security_event("banned_login_rejected", request, actor_id=user_id, email=email)
        raise HTTPException(status_code=403, detail="This account is banned. Contact an administrator.")

    refresh_token = str(data.get("refresh_token") or "")
    access_token = str(data.get("access_token") or "")
    if not refresh_token or not access_token:
        raise HTTPException(status_code=502, detail="Supabase did not return a token pair.")
    expires_at = (datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)).isoformat()
    saved = execute_query(db.table("app_sessions").insert({
        "user_id": user_id, "refresh_token_hash": token_hash(refresh_token),
        "access_token_hash": token_hash(access_token), "device_name": agent[:120],
        "ip_address": ip, "user_agent": agent, "expires_at": expires_at,
    }).select("id"))
    session_id = saved.data[0]["id"] if saved.data else None
    if not session_id:
        raise HTTPException(status_code=502, detail="Could not create a secure session.")
    execute_query(db.table("login_attempts").insert({
        "email": email, "ip_address": ip, "succeeded": True,
    }))
    record_activity(user_id, "login", "session", session_id, request)
    return ({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(data.get("expires_in") or 900),
        "session_id": session_id,
        "user": {
            "id": user_id, "email": user.get("email") or email,
            "full_name": user.get("full_name") or "", "role": user.get("role") or "student",
        },
    }, refresh_token)


def refresh(refresh_token: str, request: Request) -> tuple[dict[str, Any], str]:
    db = get_database()
    old_hash = token_hash(refresh_token)
    result = execute_query(
        db.table("app_sessions").select("id,user_id,expires_at,revoked_at")
        .eq("refresh_token_hash", old_hash).limit(1)
    )
    if not result.data:
        record_security_event("refresh_token_rejected", request)
        raise HTTPException(status_code=401, detail="Refresh token is invalid or has already been rotated.")
    row = result.data[0]
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
    if row.get("revoked_at") or expires_at <= now:
        raise HTTPException(status_code=401, detail="Session has expired or was revoked.")
    data = _auth_request("token?grant_type=refresh_token", {"refresh_token": refresh_token})
    new_refresh = str(data.get("refresh_token") or "")
    access = str(data.get("access_token") or "")
    if not new_refresh or not access:
        raise HTTPException(status_code=502, detail="Supabase did not rotate the token pair.")
    profile = execute_query(
        db.table("profiles").select("is_banned").eq("id", row["user_id"]).limit(1)
    )
    if not profile.data or profile.data[0].get("is_banned"):
        execute_query(db.table("app_sessions").update({"revoked_at": now.isoformat()}).eq("id", row["id"]))
        raise HTTPException(status_code=403, detail="This account is banned or unavailable.")
    update = execute_query(db.table("app_sessions").update({
        "refresh_token_hash": token_hash(new_refresh),
        "access_token_hash": token_hash(access),
        "last_seen_at": now.isoformat(),
        "expires_at": (now + timedelta(days=REFRESH_DAYS)).isoformat(),
    }).eq("id", row["id"]).eq("refresh_token_hash", old_hash).select("id"))
    if not update.data:
        record_security_event("refresh_token_reuse_detected", request, actor_id=row["user_id"])
        raise HTTPException(status_code=401, detail="Refresh token was already used.")
    record_activity(row["user_id"], "token_refresh", "session", row["id"], request)
    return ({
        "access_token": access, "token_type": "bearer",
        "expires_in": int(data.get("expires_in") or 900), "session_id": row["id"],
    }, new_refresh)


def logout(refresh_token: str | None, request: Request) -> None:
    if not refresh_token:
        return
    result = execute_query(
        get_database().table("app_sessions").select("id,user_id")
        .eq("refresh_token_hash", token_hash(refresh_token)).limit(1)
    )
    if result.data:
        row = result.data[0]
        execute_query(get_database().table("app_sessions").update({
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", row["id"]))
        record_activity(row["user_id"], "logout", "session", row["id"], request)


def list_sessions(user_id: str) -> list[dict[str, Any]]:
    result = execute_query(
        get_database().table("app_sessions")
        .select("id,device_name,ip_address,user_agent,created_at,last_seen_at,expires_at,revoked_at")
        .eq("user_id", user_id).order("created_at", desc=True)
    )
    return result.data or []


def revoke_session(user_id: str, session_id: str, request: Request) -> None:
    result = execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).eq("user_id", user_id).is_("revoked_at", "null").select("id")
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Active session not found.")
    record_activity(user_id, "session_revoked", "session", session_id, request)


def revoke_others(user_id: str, current_session_id: str | None, request: Request) -> int:
    query = get_database().table("app_sessions").update({
        "revoked_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user_id).is_("revoked_at", "null")
    if current_session_id:
        query = query.neq("id", current_session_id)
    result = execute_query(query.select("id"))
    count = len(result.data or [])
    record_activity(user_id, "other_sessions_revoked", "session", request=request, details={"count": count})
    return count


def revoke_all(user_id: str, request: Request) -> int:
    result = execute_query(get_database().table("app_sessions").update({
        "revoked_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user_id).is_("revoked_at", "null").select("id"))
    count = len(result.data or [])
    record_activity(user_id, "all_sessions_revoked", "session", request=request, details={"count": count})
    return count


def update_profile(user_id: str, full_name: str, request: Request) -> dict[str, Any]:
    result = execute_query(get_database().table("profiles").update({
        "full_name": full_name.strip(), "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user_id).select("id,email,full_name,role"))
    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    record_activity(user_id, "profile_updated", "user", user_id, request)
    return result.data[0]


def change_password(user_id: str, email: str, current_password: str,
                    new_password: str, request: Request) -> None:
    data = _auth_request("token?grant_type=password", {
        "email": email, "password": current_password,
    })
    access = str(data.get("access_token") or "")
    if not access:
        raise HTTPException(status_code=401, detail="Current password could not be verified.")
    try:
        response = httpx.put(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers={"apikey": str(SUPABASE_ANON_KEY), "Authorization": f"Bearer {access}",
                     "Content-Type": "application/json"},
            json={"password": new_password}, timeout=15.0,
        )
        if not response.is_success:
            raise HTTPException(status_code=400, detail="Password update was rejected by Supabase Auth.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Password update service is unavailable.") from exc
    revoke_all(user_id, request)
    record_activity(user_id, "password_changed", "user", user_id, request)
