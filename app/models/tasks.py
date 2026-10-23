from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.priority import Priority
from app.models.status import Status

if TYPE_CHECKING:
    from app.models.projects import Project
    from app.models.users import User


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str]
    status: Mapped[Status] = mapped_column(index=True, nullable=False)
    priority: Mapped[Priority] = mapped_column(default=Priority.MEDIUM, nullable=False)
    assignee_id: Mapped[int] = mapped_column(index=True)
    due_date: Mapped[datetime] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    user: Mapped["User"] = relationship(back_populates="tasks")

    __table_args__ = (
        CheckConstraint("status IN ('Новая', 'В работе', 'Выполнена')", name="check_status_valid"),
        CheckConstraint(
            "priority IN ('Средний', 'Низкий', 'Высокий')", name="check_priority_valid"
        ),
    )
