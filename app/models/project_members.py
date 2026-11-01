from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.projects import Project
    from app.models.users import User


class ProjectsMember(Base):
    __tablename__ = "projects_members"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", name="projects_fk", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="users_fk", ondelete="CASCADE")
    )
    role: Mapped[str]

    project: Mapped["Project"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="project_memberships")

    __table_args__ = (Index("idx_project_user", "user_id", "project_id", unique=True),)
