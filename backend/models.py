"""Typed domain models returned by the Supabase data layer.

The PostgreSQL table definitions and constraints are maintained in migrations/.
These TypedDicts describe the Python data exchanged by the API and services.
"""

from typing import Literal
from typing_extensions import TypedDict

Role = Literal["student", "staff", "admin"]


class CurrentUser(TypedDict):
    id: str
    email: str
    full_name: str
    role: Role


class ServiceRequestRecord(TypedDict, total=False):
    id: int
    user_id: str | None
    title: str
    description: str
    category: str
    status: str
    created_at: str
    updated_at: str
