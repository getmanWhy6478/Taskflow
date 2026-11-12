from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import get_task_with_access, get_task_with_access_only_view, require_user
from app.forms.comment import CommentForm
from app.forms.tasks import TaskForm
from app.models import Priority, Status, Task, User
from app.services import comment_services as comment_service
from app.services import permission_services as permission_service
from app.services import project_services as project_services
from app.services import task_services as task_service
from app.templates.templates import templates

from app.services.activity_services import log_activity

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{t_id}")
def get_task(
    request: Request,
    t_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    task: Task = Depends(get_task_with_access_only_view),
):
    comments = task_service.get_tasks_comments(db, task)
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")
    return templates.TemplateResponse(
        request,
        "tasks/detail.html",
        {
            "user": user,
            "task": task,
            "comments": comments,
            "flash_message": flash_message,
            "flash_type": flash_type,
        },
    )


@router.get("/{t_id}/edit")
def edit_task_page(
    t_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    task: Task = Depends(get_task_with_access),
):
    if not permission_service.can_edit_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    project = project_services.get_project_by_id(db, task.project_id)
    available_members = project_services.get_project_members(db, project)
    return templates.TemplateResponse(
        request,
        "tasks/edit.html",
        {
            "user": user,
            "task": task,
            "field_errors": None,
            "statuses": Status,
            "priorities": Priority,
            "members": available_members
        },
    )


@router.post("/{t_id}/edit")
def edit_task(
    t_id: int,
    request: Request,
    assignee_id: str = Form(""),
    due_date: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    status: Status = Form(...),
    priority: Priority = Form(...),
    task: Task = Depends(get_task_with_access),
):
    title = title.lower()
    description = description.lower()
    assignee_id = int(assignee_id) if assignee_id else None
    due_date = date.fromisoformat(due_date) if due_date else None
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
            field = error["loc"][0]
            msg = error["msg"]
            field_errors.setdefault(field, []).append(msg)
        return templates.TemplateResponse(
            request,
            "tasks/edit.html",
            {
                "field_errors": field_errors,
                "user": user,
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "assignee_id": assignee_id,
                "due_date": due_date,
            },
        )
    task_service.update_task(db, task, form)
    log_activity(
        db, task.project.id, user.id,
        "task_updated", "task", task.id,
        f"Задача {task.title} была изменена. Название: {title},  Статус: {status}, Приоритет: {priority},"
        f" Назначенный: {db.get(User, assignee_id).display_name}, Выполнить до: {due_date}",
    )
    request.session["flash_message"] = "Задача изменена!"
    request.session["flash_type"] = "success"
    response = RedirectResponse(f"/tasks/{t_id}", status_code=303)
    return response


@router.post("/{t_id}/status")
def edit_status(
    request: Request,
    t_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    status: str = Form(...),
    task: Task = Depends(get_task_with_access),
):
    if not permission_service.can_edit_task_status(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")

    allowed_transitions = {
        "Новая": ["В работе"],
        "В работе": ["Выполнена"],
        "Выполнена": ["В работе"],
    }

    current_status = task.status.value
    next_status = status
    project = project_services.get_project_by_id(db, task.project_id)
    filters = request.session.pop(f"filters_{project.id}", {})

    redirect_url = f"/projects/{project.id}/tasks"
    params = []
    for key, value in filters.items():
        if value is not None and value != "":
            params.append(f"{key}={value}")

    if params:
        redirect_url += "?" + "&".join(params)
    if next_status not in allowed_transitions[current_status]:
        request.session["flash_message"] = f"Переход из '{current_status}' в '{next_status}' не разрешён"
        request.session["flash_type"] = "warning"
        return RedirectResponse(redirect_url, status_code=303)
    task_service.update_task_status(db, task, next_status)
    request.session["flash_message"] = "Статус изменён!"
    request.session["flash_type"] = "success"

    log_activity(
        db, task.project.id, user.id,
        "task_updated_status", "task", task.id,
        f"Статус задачи {task.title} изменён на: {next_status}",
    )
    return RedirectResponse(
        redirect_url,
        status_code=303,
    )


@router.post("/{t_id}/delete")
def delete_task(
    request: Request,
    t_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    task: Task = Depends(get_task_with_access),
):
    if not permission_service.can_delete_task(user, task):
        raise HTTPException(status_code=403, detail="Нет прав")
    task_service.delete_task(db, task)
    request.session["flash_message"] = "Задачи больше нет!"
    request.session["flash_type"] = "success"
    response = RedirectResponse("/projects", status_code=303)
    log_activity(
        db, task.project.id, user.id,
        "task_deleted", "task", task.id,
        f"Задача {task.title} была удалена",
    )
    return response


@router.post("/{t_id}/comments")
def add_comment(
    request: Request,
    t_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    text: str = Form(...),
    task: Task = Depends(get_task_with_access),
):
    form = CommentForm(text=text)
    comment_service.create_comment(db, form, task, user)
    request.session["flash_message"] = "Вы оставили комментарий!"
    request.session["flash_type"] = "success"
    response = RedirectResponse(f"/tasks/{t_id}", status_code=303)
    return response
