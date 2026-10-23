from pydantic import BaseModel, Field, field_validator


class RegisterForm(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    email: str = Field(min_length=10, max_length=50)
    display_name: str = Field(min_length=3, max_length=50)

    @classmethod
    @field_validator("password")
    def validate_password(cls, value):
        if value.isdigit():
            raise ValueError("Password must contain at least one non-digit character")
        return value

    @classmethod
    @field_validator("email")
    def validate_email(cls, value):
        if "@" not in value:
            raise ValueError("Email must contain '@' characters")
        return value
