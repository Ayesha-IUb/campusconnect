"""Application entry point for the CampusConnect FastAPI backend."""

from fastapi import FastAPI

from routers import auth, health, requests

app = FastAPI(
    title="CampusConnect API",
    description="University Service Request Management API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(requests.router)
