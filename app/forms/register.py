import re

from pydantic import BaseModel, Field, field_validator, EmailStr


class RegisterForm(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: EmailStr
    display_name: str = Field(min_length=3, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Za-zА-Яа-яЁё]", value):
            raise ValueError("Password must contain at least one non-digit character")
        return value
