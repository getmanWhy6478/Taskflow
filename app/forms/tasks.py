from datetime import date

from pydantic import BaseModel, Field

from app.models.priority import Priority


class TaskForm(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Priority = Priority.MEDIUM
    assignee_id: int | None = None
    due_date: date | None = None
