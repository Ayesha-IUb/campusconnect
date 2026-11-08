"""Typed descriptions of rows returned by the Supabase database.

CampusConnect uses Supabase Postgres directly rather than an ORM. These
TypedDicts document the database records without adding a second ORM layer.
"""

from typing import Literal, TypedDict

Role = Literal["student", "staff", "admin"]
Category = Literal["IT Support", "Classroom", "Facilities", "Library", "Other"]
RequestStatus = Literal["Pending", "In Progress", "Resolved", "Rejected"]


class UserProfileRecord(TypedDict, total=False):
    id: str
    email: str
    full_name: str
    role: Role


class ServiceRequestRecord(TypedDict, total=False):
    id: int
    user_id: str | None
    title: str
    description: str
    category: Category
    status: RequestStatus
    created_at: str
    updated_at: str
