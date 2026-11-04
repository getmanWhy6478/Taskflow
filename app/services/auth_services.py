from itsdangerous import URLSafeTimedSerializer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.forms.register import RegisterForm
from app.models import User

session_serializer = URLSafeTimedSerializer(settings.secret_key)

hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(input_password: str, hashed_password: str) -> bool:
    return hasher.verify(input_password, hashed_password)


def add_user(form: RegisterForm, db: Session, hashed_password: str) -> None:
    user = User(
        username=form.username,
        password_hash=hashed_password,
        email=form.email,
        display_name=form.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return


def is_user_already_registered(db: Session, form: RegisterForm) -> bool:
    return (
        db.query(User).filter_by(username=form.username).first() is not None
        or db.query(User).filter_by(email=form.email).first() is not None
    )
