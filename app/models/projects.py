from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project_members import ProjectsMember
    from app.models.tasks import Task
    from app.models.users import User


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None]
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)

    task: Mapped[list["Task"]] = relationship(
        back_populates="project", passive_deletes=True, cascade="all, delete-orphan"
    )

    members: Mapped[list["User"]] = relationship(
        back_populates="project", secondary="projects_members", viewonly=True
    )

    memberships: Mapped[list["ProjectsMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    owner: Mapped["User"] = relationship(back_populates="my_project")
