"""Typed domain records for the CampusConnect application."""
from typing import Literal, TypedDict

Role = Literal["student", "staff", "admin"]


class CurrentUser(TypedDict, total=False):
    id: str
    email: str
    full_name: str
    role: Role
    session_id: str | None
    is_banned: bool


class ServiceRequestRecord(TypedDict, total=False):
    id: int
    user_id: str | None
    group_id: str | None
    assigned_to: str | None
    title: str
    description: str
    category: str
    status: str
    created_at: str
    updated_at: str


class GroupRecord(TypedDict, total=False):
    id: str
    name: str
    description: str
    owner_id: str
    created_at: str
    updated_at: str
