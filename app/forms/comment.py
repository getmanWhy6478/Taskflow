from pydantic import BaseModel, Field


class CommentForm(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
