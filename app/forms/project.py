from pydantic import BaseModel, Field


class ProjectForm(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
