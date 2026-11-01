import re
from pydantic import BaseModel, Field, field_validator


class ChangePassword(BaseModel):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if value != "" and not re.search(r"[A-Za-zА-Яа-яЁё]", value):
            raise ValueError("Password must contain at least one non-digit character")
        return value