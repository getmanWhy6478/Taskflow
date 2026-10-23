from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tasks import Task


def search(db: Session, query: str) -> list[Task]:
    found = select(Task).where(Task.title.ilike(f"%{query}%"))
    return list(db.scalars(found))
