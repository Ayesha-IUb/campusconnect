"""Pydantic schemas for admin moderation and bulk actions."""
from pydantic import BaseModel, Field

from app.core.types import Role


class RoleChange(BaseModel):
    role: Role


class BanInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class BulkUserAction(BaseModel):
    user_ids: list[str] = Field(min_length=1, max_length=50)
    reason: str = Field(default="Bulk action by administrator", max_length=500)


class BulkDeleteInput(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=50)


class BulkRequestDeleteInput(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=50)
