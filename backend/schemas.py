"""Pydantic request and response schemas used by the API."""

from pydantic import BaseModel, ConfigDict, Field

from models import Category, RequestStatus, Role


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


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: Role


class ServiceRequestResponse(BaseModel):
    id: int
    user_id: str | None = None
    title: str
    description: str
    category: Category
    status: RequestStatus
    created_at: str
    updated_at: str


class DeleteResponse(BaseModel):
    message: str
    id: int
