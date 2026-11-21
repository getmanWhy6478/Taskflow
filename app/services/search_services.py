from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, User

def search_user_by_username(db: Session, username: str) -> User:
    user = select(User).where(User.username == username)
    return db.scalar(user)
