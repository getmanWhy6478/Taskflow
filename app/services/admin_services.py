from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import User, Task


def get_all_users(db: Session) -> list[User]:
    users = select(User).order_by(User.id)
    return list(db.scalars(users))

def get_user_tasks(db: Session) -> dict:
    found = (
        select(
            Task.author_id,
            func.count(Task.id).label("task_count")
        )
        .group_by(Task.author_id)
    )

    return {row.author_id: row.task_count for row in db.execute(found).all()}


def ban_user(db: Session, user: User):
    user.is_banned = True
    db.commit()
    db.refresh(user)
    return


def unban_user(db: Session, user: User):
    user.is_banned = False
    db.commit()
    db.refresh(user)
    return


def admin_user(db: Session, user: User):
    user.is_admin = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return


def unadmin_user(db: Session, user: User):
    user.is_admin = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return
