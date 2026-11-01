from sqlalchemy.orm import Session

from app.forms.change_form import ChangeUser
from app.forms.change_password_form import ChangePassword
from app.models import User
from app.services import auth_services


def change_name(db: Session, user: User, form: ChangeUser) -> None:
    user.display_name = form.username
    db.add(user)
    db.commit()
    db.refresh(user)
    return

def change_password(db: Session, user: User, form: ChangePassword) -> None:
    hashed_password = auth_services.hash_password(form.password)
    user.password_hash = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    return