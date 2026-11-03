
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from supabase import create_client

# Load credentials from backend/.env (local) or hosting environment.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# This privileged client stays on the backend only.
supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(
    title="CampusConnect API",
    description="University Service Request Management API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

Category = Literal[
    "IT Support",
    "Classroom",
    "Facilities",
    "Library",
    "Other",
]

RequestStatus = Literal[
    "Pending",
    "In Progress",
    "Resolved",
    "Rejected",
]

APP_ROLES = {"student", "staff", "admin"}


class RequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: Category = "Other"


class RequestUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: Category
    status: RequestStatus


def get_database():
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )
    return supabase


def execute_query(query_builder: Any) -> Any:
    try:
        return query_builder.execute()
    except Exception as exc:
        print("Supabase query failed:", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database request failed.",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
    """Verify the Supabase access token and load the user's trusted app role."""
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
        "role": role,
    }


# HEALTH CHECK - public
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "database_configured": supabase is not None,
    }


# CURRENT USER - authenticated
@app.get("/api/me")
def get_me(current_user: dict[str, str] = Depends(get_current_user)):
    return current_user


# CREATE - students and admins can submit a request.
@app.post("/api/requests", status_code=status.HTTP_201_CREATED)
def create_request(
    request: RequestCreate,
    current_user: dict[str, str] = Depends(get_current_user),
):
    if current_user["role"] not in {"student", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and admins can create requests.",
        )

    db = get_database()
    payload = request.model_dump()
    payload["user_id"] = current_user["id"]
    payload["status"] = "Pending"

    result = execute_query(
        db.table("service_requests").insert(payload)
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create service request.",
        )

    return result.data[0]


# READ LIST - students see only their requests; staff/admin see all.
@app.get("/api/requests")
def get_all_requests(
    current_user: dict[str, str] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    db = get_database()
    query = db.table("service_requests").select("*")

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.order("created_at", desc=True))
    return result.data or []


# READ SINGLE - students can only open their own requests.
@app.get("/api/requests/{request_id}")
def get_request(
    request_id: int,
    current_user: dict[str, str] = Depends(get_current_user),
):
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.limit(1))

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    return result.data[0]


# UPDATE - students may edit their own pending request without changing status.
# Staff may change status only. Admins may edit all request fields.
@app.put("/api/requests/{request_id}")
def update_request(
    request_id: int,
    request: RequestUpdate,
    current_user: dict[str, str] = Depends(get_current_user),
):
    db = get_database()
    query = db.table("service_requests").select("*").eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"])

    result = execute_query(query.limit(1))

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    existing = result.data[0]
    payload = request.model_dump()
    role = current_user["role"]

    if role == "student":
        if existing.get("status") != "Pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can edit only your own pending requests.",
            )
        if payload["status"] != existing.get("status"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot change request status.",
            )

    elif role == "staff":
        unchanged_fields = (
            payload["title"] == existing.get("title")
            and payload["description"] == existing.get("description")
            and payload["category"] == existing.get("category")
        )
        if not unchanged_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff can update request status only.",
            )

    elif role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update requests.",
        )

    updated = execute_query(
        db.table("service_requests")
        .update(payload)
        .eq("id", request_id)
        .select("*")
    )

    if not updated.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found.",
        )

    return updated.data[0]


# DELETE - students may delete their own pending requests; admins may delete any.
@app.delete("/api/requests/{request_id}")
def delete_request(
    request_id: int,
    current_user: dict[str, str] = Depends(get_current_user),
):
    if current_user["role"] == "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members cannot delete requests.",
        )

    db = get_database()
    query = db.table("service_requests").delete().eq("id", request_id)

    if current_user["role"] == "student":
        query = query.eq("user_id", current_user["id"]).eq("status", "Pending")
    elif current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete requests.",
        )

    result = execute_query(query.select("id"))

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending service request not found.",
        )

    return {
        "message": "Service request deleted successfully.",
        "id": request_id,
    }
