
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from supabase import create_client

# Load credentials from backend/.env
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Connect to Supabase when credentials are available
supabase = None

if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


app = FastAPI(
    title="CampusConnect API",
    description="University Service Request Management API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)


# Allowed categories and statuses
Category = Literal[
    "IT Support",
    "Classroom",
    "Facilities",
    "Library",
    "Other"
]

RequestStatus = Literal[
    "Pending",
    "In Progress",
    "Resolved",
    "Rejected"
]


# Model for creating a request
class RequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: Category = "Other"


# Model for updating a request
class RequestUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: Category
    status: RequestStatus


# Check database configuration
def get_database():
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    return supabase


# Execute each database query exactly once
def execute_query(query_builder: Any) -> Any:
    try:
        return query_builder.execute()
    except Exception as exc:
        print("Supabase query failed:", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Database request failed."
        ) from exc


# HEALTH CHECK
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "database_configured": supabase is not None
    }

# CREATE: Add a new service request
@app.post(
    "/api/requests",
    status_code=status.HTTP_201_CREATED
)
def create_request(request: RequestCreate):

    db = get_database()

    result = execute_query(
        db.table("service_requests")
        .insert(request.model_dump())
    )

    if not result.data:
        raise HTTPException(
            status_code=500,
            detail="Could not create service request."
        )

    return result.data[0]


# READ LIST: Retrieve all requests
@app.get("/api/requests")
def get_all_requests() -> list[dict[str, Any]]:

    db = get_database()

    result = execute_query(
        db.table("service_requests")
        .select("*")
        .order("created_at", desc=True)
    )

    return result.data or []


# READ SINGLE: Retrieve one request
@app.get("/api/requests/{request_id}")
def get_request(request_id: int):

    db = get_database()

    result = execute_query(
        db.table("service_requests")
        .select("*")
        .eq("id", request_id)
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Service request not found."
        )

    return result.data[0]


# UPDATE: Modify an existing request
@app.put("/api/requests/{request_id}")
def update_request(request_id: int, request: RequestUpdate):

    db = get_database()

    result = execute_query(
        db.table("service_requests")
        .update(request.model_dump())
        .eq("id", request_id)
        .select("*")
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Service request not found."
        )

    return result.data[0]


# DELETE: Remove a request
@app.delete("/api/requests/{request_id}")
def delete_request(request_id: int):

    db = get_database()

    result = execute_query(
        db.table("service_requests")
        .delete()
        .eq("id", request_id)
        .select("id")
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Service request not found."
        )

    return {
        "message": "Service request deleted successfully.",
        "id": request_id
    }
