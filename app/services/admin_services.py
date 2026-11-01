from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User


def get_all_users(db: Session) -> list[User]:
    users = select(User).order_by(User.id)
    return list(db.scalars(users))


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
