from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models import Comment, Project, ProjectsMember, Task


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_banned: Mapped[bool] = mapped_column(default=False, server_default=sa.false())
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    task: Mapped[list["Task"]] = relationship(back_populates="user", foreign_keys="Task.author_id")
    comment: Mapped[list["Comment"]] = relationship(back_populates="user")

    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )

    project: Mapped[list["Project"]] = relationship(
        back_populates="members", secondary="projects_members", viewonly=True
    )

    project_memberships: Mapped[list["ProjectsMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    my_project: Mapped["Project"] = relationship(back_populates="owner")

    def get_role_in_project(self, project_id: int) -> str | None:
        for membership in self.project_memberships:
            if membership.project_id == project_id:
                return membership.role
        return None
