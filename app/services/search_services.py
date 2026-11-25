from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models import Task, User

def search_user_by_username_or_email(db: Session, username: str) -> User:
    user = select(User).where(or_(User.username == username, User.email == username))
    return db.scalar(user)
