"""Authentication endpoints and secure refresh-cookie session handling."""
import os
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from app.auth.schemas import LoginInput, RegisterInput
from app.auth import service as auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
COOKIE_NAME = "campusconnect_refresh"
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))


def _cookie_options(request: Request) -> dict:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    secure = request.url.scheme == "https" or forwarded_proto == "https"
    return {
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "path": "/api/auth",
        "max_age": REFRESH_DAYS * 24 * 60 * 60,
    }


def _set_refresh_cookie(response: Response, token: str, request: Request) -> None:
    response.set_cookie(COOKIE_NAME, token, **_cookie_options(request))


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: RegisterInput):
    return auth_service.register(payload.email, payload.password, payload.full_name)


@router.post("/login")
def login(payload: LoginInput, request: Request, response: Response):
    result, refresh_token = auth_service.login(payload.email, payload.password, request)
    _set_refresh_cookie(response, refresh_token, request)
    return result


@router.post("/refresh")
def refresh(request: Request, response: Response,
            refresh_token: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session is missing.")
    result, new_refresh = auth_service.refresh(refresh_token, request)
    _set_refresh_cookie(response, new_refresh, request)
    return result


@router.post("/logout")
def logout(request: Request, response: Response,
           refresh_token: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    auth_service.logout(refresh_token, request)
    response.delete_cookie(
        COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto") == "https",
    )
    return {"message": "Signed out and refresh session revoked."}
