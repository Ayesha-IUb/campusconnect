"""User profile and password schemas."""
from pydantic import BaseModel, Field, field_validator


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if (
            not any(c.islower() for c in value)
            or not any(c.isupper() for c in value)
            or not any(c.isdigit() for c in value)
        ):
            raise ValueError(
                "New password must contain uppercase, lowercase and a number."
            )
        return value
