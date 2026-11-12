from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    action: Mapped[str] = mapped_column(String(50))

    target_type: Mapped[str] = mapped_column(String(50), nullable=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)

    details: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    project = relationship("Project", back_populates="activities")
    user = relationship("User", back_populates="activities")