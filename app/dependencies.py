from urllib.parse import quote

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.forms import project
from app.models import User, Project, Task, Comment



class AuthRequiredException(HTTPException):
    def __init__(self, next_page: str = ""):
        super().__init__(
            status_code=401,
            detail="Требуется авторизация",
        )
        self.next_page = next_page


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def require_user(
    request: Request, user: User | None = Depends(get_current_user)
) -> User | RedirectResponse:
    if user is None:
        next_page = request.url.path
        if request.url.query:
            next_page += f"?{request.url.query}"

        raise AuthRequiredException(next_page=next_page)

    if user.is_banned:
        request.session.clear()
        raise HTTPException(403, "Ваш аккаунт заблокирован")
    return user


def require_project_member(user: User | None = Depends(require_user)) -> User:
    if user not in project.member:
        raise HTTPException(status_code=403)
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Доступ запрещён. Требуются права администратора.")
    return user


def get_project_with_access(
    p_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.get(Project, p_id)

    if project is None:
        raise HTTPException(404, "Проект не найден")

    if user not in project.members and not user.is_admin:
        raise HTTPException(403, "Проект не найден или у вас нет доступа")

    return project


def get_task_with_access(
    t_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.get(Task, t_id)

    if task is None:
        raise HTTPException(404, "Проект не найден")

    if user not in task.project.members and not user.is_admin:
        raise HTTPException(403, "Задача не найдена или у вас нет доступа")

    return task


def delete_comment_with_access(
    c_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Comment:
    comment = db.get(Comment, c_id)

    if comment is None:
        raise HTTPException(404, "Комментарий не найден")

    if user != comment.user and not user.is_admin:
        raise HTTPException(403, "Задача не найдена или у вас нет доступа")

    return comment
