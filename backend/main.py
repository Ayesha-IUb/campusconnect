"""CampusConnect FastAPI application entrypoint."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import supabase
from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.groups.router import router as groups_router
from app.requests.router import router as requests_router
from app.users.router import router as users_router

app = FastAPI(
    title="CampusConnect API",
    description="University Service Request Management API",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

allowed_origins = [
    origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,https://campusconnect-two-ivory.vercel.app"
    ).split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(requests_router)
app.include_router(groups_router)
app.include_router(admin_router)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/health", tags=["Health"])
def health() -> dict[str, bool | str]:
    return {"status": "ok", "database_configured": supabase is not None}
