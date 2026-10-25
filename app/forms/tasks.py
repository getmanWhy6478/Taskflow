from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.priority import Priority
from app.models.status import Status


class TaskForm(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    status: Status
    priority: Priority = Priority.MEDIUM
    assignee_id: int | None = None
    due_date: datetime | None = None

    @classmethod
    @field_validator("due_date")
    def due_date_validator(cls, value):
        if value < datetime.now():
            raise ValueError("Due date must be in the future")
        return value
