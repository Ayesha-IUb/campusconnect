"""Pydantic request schemas used for API validation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
