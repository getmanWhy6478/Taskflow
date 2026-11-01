from urllib.parse import quote

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session


from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import User
from app.services import auth_services


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("session")
    if not token:
        return None
    user_id = auth_services.read_session_token(token)
    return db.get(User, user_id) if user_id else None


def require_user(request: Request, user: User | None = Depends(get_current_user)) -> User|RedirectResponse:
    if user is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if user.is_banned:
        request.session.clear()
        return RedirectResponse(
            "blocked_page",
            status_code=303,
        )
    return user

def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Доступ запрещён. Требуются права администратора.")
    return user
