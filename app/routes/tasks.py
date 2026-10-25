from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user
from app.forms.comment import CommentForm
from app.forms.tasks import TaskForm
from app.models.priority import Priority
from app.models.status import Status
from app.models.users import User
from app.services import comment_services as comment_service
from app.services import permission_services as permission_service
from app.services import task_services as task_service
from app.templates.templates import templates

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("{t_id}")
def get_tasks(
    request: Request, t_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    task = task_service.get_task_by_id(db, t_id)
    return templates.TemplateResponse(request, "projects/card.html", {"user": user, "task": task})


@router.get("{t_id}/edit")
def edit_task_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "task/edit.html", {"user": user})


@router.post("{t_id}/edit")
def edit_task(
    t_id: int,
    request: Request,
    assignee_id: int | None = None,
    due_date: datetime | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(...),
    status: Status = Form(...),
    priority: Priority = Form(...),
):
    task = task_service.get_task_by_id(db, t_id)
    if not permission_service.can_edit_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    try:
        form = TaskForm(
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            due_date=due_date,
        )
        task_service.update_task(db, task, form)
        response = RedirectResponse("/tasks")
        return response
    except ValueError:
        return templates.TemplateResponse(request, "task/edit.html", {"user": user})


@router.post("{t_id}/status")
def edit_status(
    t_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    status: Status = Form(...),
):
    task = task_service.get_task_by_id(db, t_id)
    if not permission_service.can_edit_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    if (
        status == "В работе"
        or (status == "Выполнена" and task.status == "В работе")
        or (status == task.status)
    ):
        task_service.update_task_status(db, task, status)


@router.post("/{t_id}/delete")
def delete_task(
    request: Request, t_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    task = task_service.get_task_by_id(db, t_id)
    if not permission_service.can_edit_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    task_service.delete_task(db, task)
    response = RedirectResponse("/projects")
    return response


@router.post("/{t_id}/comments")
def add_comment(
    request: Request,
    t_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    text: str = Form(...),
):
    task = task_service.get_task_by_id(db, t_id)
    form = CommentForm(text=text)
    comment_service.create_comment(db, form, task, user)
