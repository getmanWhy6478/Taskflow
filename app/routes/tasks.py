from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user
from app.forms.comment import CommentForm
from app.forms.tasks import TaskForm
from app.models import Priority, Status, User, Task
from app.services import (comment_services as comment_service, permission_services as permission_service,
                          task_services as task_service, project_services as project_services)
from app.templates.templates import templates

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{t_id}")
def get_task(
    request: Request, t_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    task = task_service.get_task_by_id(db, t_id)
    comments = task_service.get_tasks_comments(db, task)
    return templates.TemplateResponse(request, "tasks/detail.html", {"user": user, "task": task, "comments": comments})


@router.get("/{t_id}/edit")
def edit_task_page(t_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    task = db.get(Task, t_id)
    project = project_services.get_project_by_id(db, task.project_id)
    available_members = project_services.get_project_members(db, project)
    return templates.TemplateResponse(request, "tasks/edit.html", {"user": user, "task": task, "field_errors": None,
                                                                   "statuses": Status, "priorities": Priority, "members": available_members})


@router.post("/{t_id}/edit")
def edit_task(
    t_id: int,
    request: Request,
    assignee_id: str = Form(""),
    due_date: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(...),
    status: Status = Form(...),
    priority: Priority = Form(...),
):
    title = title.lower()
    description = description.lower()
    assignee_id = int(assignee_id) if assignee_id else None
    due_date = date.fromisoformat(due_date) if due_date else None
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
    except ValidationError as e:
        field_errors = {}
        for error in e.errors():
            field = error['loc'][0]
            msg = error['msg']
            field_errors.setdefault(field, []).append(msg)
        return templates.TemplateResponse(request, "task/edit.html", {"field_errors": field_errors, "user": user,
        "title":title,
        "description":description,
        "status" : status,
        "priority" : priority,
        "assignee_id" : assignee_id,
        "due_date" : due_date
        })
    task_service.update_task(db, task, form)
    response = RedirectResponse(f"/tasks/{t_id}", status_code=303)
    return response


@router.post("/{t_id}/status")
def edit_status(
    t_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    status: str = Form(...),
):
    task = task_service.get_task_by_id(db, t_id)
    if not permission_service.can_edit_task_status(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")

    ALLOWED_TRANSITIONS = {
        "Новая": ["В работе"],
        "В работе": ["Выполнена"],
        "Выполнена": ["В работе"]
    }

    current_status = task.status.value
    next_status = Status[status].value

    if next_status not in ALLOWED_TRANSITIONS[current_status]:
        raise HTTPException(
            400,
            f"Переход из '{current_status}' в '{next_status}' не разрешён"
        )
    print(next_status)
    task_service.update_task_status(db, task, next_status)
    return RedirectResponse(
        f"/tasks/{t_id}",
        status_code=303,
    )


@router.post("/{t_id}/delete")
def delete_task(
    t_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    task = task_service.get_task_by_id(db, t_id)
    if not permission_service.can_delete_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    task_service.delete_task(db, task)
    response = RedirectResponse("/projects", status_code=303)
    return response


@router.post("/{t_id}/comments")
def add_comment(
    t_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    text: str = Form(...),
):
    task = task_service.get_task_by_id(db, t_id)
    form = CommentForm(text=text)
    comment_service.create_comment(db, form, task, user)
    response = RedirectResponse(f"/tasks/{t_id}", status_code=303)
    return response
