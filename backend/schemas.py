"""Pydantic input schemas for request validation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Category = Literal["IT Support", "Classroom", "Facilities", "Library", "Other"]
RequestStatus = Literal["Pending", "In Progress", "Resolved", "Rejected"]
Role = Literal["student", "staff", "admin"]


class RequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    category: Category = "Other"


class RequestUpdate(RequestCreate):
    status: RequestStatus = "Pending"


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(c.islower() for c in value) or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("New password must contain uppercase, lowercase and a number.")
        return value


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


class RoleChange(BaseModel):
    role: Role


class BanInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class BulkUserAction(BaseModel):
    user_ids: list[str] = Field(min_length=1, max_length=50)
    reason: str = Field(default="Bulk action by administrator", max_length=500)


class BulkDeleteInput(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=50)
