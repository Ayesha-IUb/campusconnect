"""Pydantic schemas for group and shared-request validation."""
from pydantic import BaseModel, EmailStr, Field

from app.requests.schemas import Category, RequestCreate, RequestStatus


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)


class GroupUpdate(GroupCreate):
    pass


class GroupMemberInput(BaseModel):
    email: EmailStr
    can_create_requests: bool = False
    can_edit_requests: bool = False
    can_assign_requests: bool = False


class GroupRequestCreate(RequestCreate):
    assigned_to: str | None = None


class GroupRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=5, max_length=2000)
    category: Category | None = None
    assigned_to: str | None = None
    status: RequestStatus | None = None
