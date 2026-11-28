"""Supabase Auth with server-side peppering, refresh rotation and session management."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException, Request

from app.core.database import SUPABASE_ANON_KEY, SUPABASE_SECRET_KEY, SUPABASE_URL
from app.auth import repository as auth_repo
from app.activity.service import record_activity, record_security_event

REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
# Prefer a dedicated PASSWORD_PEPPER. The server-only Supabase secret is a stable
# fallback for existing deployments; never expose either value to the frontend.
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER") or SUPABASE_SECRET_KEY


def _prepared_password(password: str) -> str:
    if not PASSWORD_PEPPER:
        raise HTTPException(status_code=503, detail="Server-side password pepper is not configured.")
    digest = hmac.new(
        PASSWORD_PEPPER.encode("utf-8"), password.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    # Supabase Auth then stores this value with its own salted bcrypt hash.
    return f"Cc!{digest}9"


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


def _update_supabase_password(access_token: str, prepared_password: str) -> None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(status_code=503, detail="Supabase Auth is not configured.")
    try:
        response = httpx.put(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}",
                     "Content-Type": "application/json"},
            json={"password": prepared_password}, timeout=15.0,
        )
        if not response.is_success:
            raise HTTPException(status_code=400, detail="Password update was rejected by Supabase Auth.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Password update service is unavailable.") from exc


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _context(request: Request) -> tuple[str, str]:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return ip[:100], request.headers.get("user-agent", "Unknown")[:500]


def register(email: str, password: str, full_name: str) -> dict[str, Any]:
    data = _auth_request("signup", {
        "email": email.strip().lower(), "password": _prepared_password(password),
        "data": {"full_name": full_name.strip()},
    })
    if data.get("access_token"):
        return {"confirmation_required": False, "message": "Account created. You can now sign in."}
    return {"confirmation_required": True, "message": "Account created. Confirm your email before signing in."}


def login(email: str, password: str, request: Request) -> tuple[dict[str, Any], str]:
    email = email.strip().lower()
    ip, agent = _context(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()

    if auth_repo.count_failed_attempts(email, ip, cutoff) >= 5:
        record_security_event("login_locked", request, email=email)
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

    try:
        data = _auth_request("token?grant_type=password", {
            "email": email, "password": _prepared_password(password),
        })
    except HTTPException:
        try:
            data = _auth_request("token?grant_type=password", {"email": email, "password": password})
            legacy_access = str(data.get("access_token") or "")
            if legacy_access:
                try:
                    _update_supabase_password(legacy_access, _prepared_password(password))
                    record_security_event(
                        "legacy_password_upgraded", request,
                        actor_id=str((data.get("user") or {}).get("id") or ""), email=email,
                    )
                except HTTPException:
                    record_security_event("legacy_password_upgrade_failed", request, email=email)
        except HTTPException:
            auth_repo.insert_login_attempt(email, ip, False)
            record_security_event("login_failed", request, email=email)
            raise

    user_id = str((data.get("user") or {}).get("id") or "")
    profile = auth_repo.get_profile(user_id)
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
    saved = auth_repo.create_session({
        "user_id": user_id, "refresh_token_hash": token_hash(refresh_token),
        "access_token_hash": token_hash(access_token), "device_name": agent[:120],
        "ip_address": ip, "user_agent": agent, "expires_at": expires_at,
    })
    session_id = saved.data[0]["id"] if saved.data else None
    if not session_id:
        raise HTTPException(status_code=502, detail="Could not create a secure session.")

    auth_repo.clear_failed_attempts(email, ip)
    auth_repo.insert_login_attempt(email, ip, True)
    record_activity(user_id, "login", "session", session_id, request)

    return ({
        "access_token": access_token, "token_type": "bearer",
        "expires_in": int(data.get("expires_in") or 900), "session_id": session_id,
        "user": {
            "id": user_id, "email": user.get("email") or email,
            "full_name": user.get("full_name") or "", "role": user.get("role") or "student",
        },
    }, refresh_token)




def refresh(refresh_token: str, request: Request) -> tuple[dict[str, Any], str]:
    old_hash = token_hash(refresh_token)
    result = auth_repo.get_session_by_refresh_hash(old_hash)
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

    profile = auth_repo.get_profile(row["user_id"])
    if not profile.data or profile.data[0].get("is_banned"):
        auth_repo.revoke_session_by_id(row["id"], now.isoformat())
        raise HTTPException(status_code=403, detail="This account is banned or unavailable.")

    update = auth_repo.rotate_session(row["id"], old_hash, {
        "refresh_token_hash": token_hash(new_refresh),
        "access_token_hash": token_hash(access),
        "last_seen_at": now.isoformat(),
        "expires_at": (now + timedelta(days=REFRESH_DAYS)).isoformat(),
    })
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
    result = auth_repo.get_session_owner_by_refresh_hash(token_hash(refresh_token))
    if result.data:
        row = result.data[0]
        auth_repo.revoke_session_by_id(row["id"], datetime.now(timezone.utc).isoformat())
        record_activity(row["user_id"], "logout", "session", row["id"], request)




def list_sessions(user_id: str) -> list[dict[str, Any]]:
    result = auth_repo.list_user_sessions(user_id)
    return result.data or []




def revoke_session(user_id: str, session_id: str, request: Request) -> None:
    result = auth_repo.revoke_one_session(
        user_id, session_id, datetime.now(timezone.utc).isoformat()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Active session not found.")
    record_activity(user_id, "session_revoked", "session", session_id, request)




def revoke_others(user_id: str, current_session_id: str | None, request: Request) -> int:
    result = auth_repo.revoke_other_sessions(
        user_id, current_session_id, datetime.now(timezone.utc).isoformat()
    )
    count = len(result.data or [])
    record_activity(user_id, "other_sessions_revoked", "session", request=request, details={"count": count})
    return count




def revoke_all(user_id: str, request: Request) -> int:
    result = auth_repo.revoke_all_sessions(
        user_id, datetime.now(timezone.utc).isoformat()
    )
    count = len(result.data or [])
    record_activity(user_id, "all_sessions_revoked", "session", request=request, details={"count": count})
    return count




def change_password(user_id: str, email: str, current_password: str,
                    new_password: str, request: Request) -> None:
    try:
        data = _auth_request("token?grant_type=password", {
            "email": email, "password": _prepared_password(current_password),
        })
    except HTTPException:
        # Compatibility for a legacy account not yet migrated by login.
        data = _auth_request("token?grant_type=password", {
            "email": email, "password": current_password,
        })
    access = str(data.get("access_token") or "")
    if not access:
        raise HTTPException(status_code=401, detail="Current password could not be verified.")
    _update_supabase_password(access, _prepared_password(new_password))
    revoke_all(user_id, request)
    record_activity(user_id, "password_changed", "user", user_id, request)
