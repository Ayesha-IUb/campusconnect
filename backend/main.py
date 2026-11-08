"""CampusConnect FastAPI application entrypoint."""

from fastapi import FastAPI

from database import supabase
from routers.requests import router as requests_router
from routers.users import router as users_router

app = FastAPI(
    title="CampusConnect API",
    description="University Service Request Management API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(users_router)
app.include_router(requests_router)


@app.get("/api/health", tags=["Health"])
def health() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "database_configured": supabase is not None,
    }
