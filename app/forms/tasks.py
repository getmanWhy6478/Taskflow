from datetime import date

from pydantic import BaseModel, Field

from app.models.priority import Priority
from app.models.status import Status


class TaskForm(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    status: Status
    priority: Priority = Priority.MEDIUM
    assignee_id: int | None = None
    due_date: date | None = None
