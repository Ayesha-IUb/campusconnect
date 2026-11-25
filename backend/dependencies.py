"""Authentication and session verification dependencies."""
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import execute_query, get_database
from models import CurrentUser, Role

bearer_scheme = HTTPBearer(auto_error=False)
APP_ROLES: set[Role] = {"student", "staff", "admin"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Sign in is required.",
                            headers={"WWW-Authenticate": "Bearer"})
    db = get_database()
    access_hash = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    try:
        verified = db.auth.get_claims(jwt=credentials.credentials)
        claims = getattr(verified, "claims", None)
        if claims is None and isinstance(verified, dict):
            claims = verified.get("claims")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.",
                            headers={"WWW-Authenticate": "Bearer"}) from exc

    if not isinstance(claims, dict) or not claims.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid access token.")

    user_id = str(claims["sub"])
    profile_result = execute_query(
        db.table("profiles").select("id,email,full_name,role,is_banned")
        .eq("id", user_id).limit(1)
    )
    if not profile_result.data:
        raise HTTPException(status_code=403, detail="User profile was not found.")
    profile = profile_result.data[0]
    if profile.get("is_banned"):
        raise HTTPException(status_code=403, detail="This account is banned.")
    role = profile.get("role")
    if role not in APP_ROLES:
        raise HTTPException(status_code=403, detail="User role is not valid.")

    session_result = execute_query(
        db.table("app_sessions").select("id")
        .eq("user_id", user_id).eq("access_token_hash", access_hash)
        .is_("revoked_at", "null").limit(1)
    )
    if not session_result.data:
        raise HTTPException(status_code=401, detail="Session expired or revoked. Please sign in again.",
                            headers={"WWW-Authenticate": "Bearer"})

    return {
        "id": user_id,
        "email": str(profile.get("email") or claims.get("email") or ""),
        "full_name": str(profile.get("full_name") or ""),
        "role": role,
        "session_id": session_result.data[0]["id"],
        "is_banned": False,
    }
