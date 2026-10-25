import re

from pydantic import BaseModel, Field, field_validator


class RegisterForm(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: str = Field(min_length=10, max_length=50)
    display_name: str = Field(min_length=3, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Za-zА-Яа-яЁё]", value):
            raise ValueError("Password must contain at least one non-digit character")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if "@" not in value:
            raise ValueError("Email must contain '@' characters")
        return value
