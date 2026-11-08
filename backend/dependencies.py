"""Shared authentication dependency for protected API routes."""

from typing import cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import execute_query, get_database
from models import Role

bearer_scheme = HTTPBearer(auto_error=False)
APP_ROLES = {"student", "staff", "admin"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
    """Verify the Supabase access token and load the trusted database role."""
    db = get_database()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        verified = db.auth.get_claims(jwt=credentials.credentials)
        claims = getattr(verified, "claims", None)
        if claims is None and isinstance(verified, dict):
            claims = verified.get("claims")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not isinstance(claims, dict) or not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(claims["sub"])
    result = execute_query(
        db.table("profiles")
        .select("id,email,full_name,role")
        .eq("id", user_id)
        .limit(1)
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile was not found. Contact an administrator.",
        )

    profile = result.data[0]
    role = profile.get("role")
    if role not in APP_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not valid.",
        )

    return {
        "id": user_id,
        "email": str(profile.get("email") or claims.get("email") or ""),
        "full_name": str(profile.get("full_name") or ""),
        "role": cast(Role, role),
    }
