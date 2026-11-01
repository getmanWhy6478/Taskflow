from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, User


def search(db: Session, query: str) -> list[Task]:
    found = select(Task).where(Task.title.ilike(f"%{query}%"))
    return list(db.scalars(found))


def search_user_by_id(db: Session, username: str) -> int:
    u_id = select(User.id).where(User.username == username)
    return db.scalar(u_id)
