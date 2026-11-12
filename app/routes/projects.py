import csv
import io
import urllib
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.database import get_db
from app.dependencies import (
    get_project_with_access,
    get_project_with_access_only_view,
    require_user,
)
from app.forms.delete import DeleteForm
from app.forms.member import MemberForm
from app.forms.project import ProjectForm
from app.forms.tasks import TaskForm
from app.models import Priority, Project, Status, User
from app.services import admin_services as admin_service
from app.services import permission_services as permission_service
from app.services import project_services as project_service
from app.services import task_services as task_service
from app.services.activity_services import log_activity
from app.templates.templates import templates

router = APIRouter(prefix="/projects", tags=["projects"])

TASKS_PER_PAGE = 10


@router.get("")
def get_projects(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    projects = project_service.get_all_projects(db, user)
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")
    return templates.TemplateResponse(
        request,
        "projects/list.html",
        {
            "user": user,
            "projects": projects,
            "flash_message": flash_message,
            "flash_type": flash_type,
        },
    )


@router.get("/create")
def create_project_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(
        request, "projects/create.html", {"user": user, "field_errors": None}
    )


@router.post("/create")
def create_project(
    request: Request,
    user: User = Depends(require_user),
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        form = ProjectForm(name=name, description=description)
    except ValidationError as e:
        field_errors = {}
        for error in e.errors():
            field = error["loc"][0]
            message = error["msg"]
            field_errors.setdefault(field, []).append(message)
        return templates.TemplateResponse(
            request,
            "projects/create.html",
            {"user": user, "fields_errors": field_errors, "name": name, "description": description},
        )
    project = project_service.create_project(db, form, user)
    response = RedirectResponse("/projects", status_code=303)
    p_m = MemberForm(member_id=user.id, role="Владелец")
    project_service.add_member(db, project, p_m)
    log_activity(
        db,
        project.id,
        user.id,
        "created",
        "project",
        project.id,
        f"Проект «{project.name}» был создан",
    )
    request.session["flash_message"] = "Проект реально создан!"
    request.session["flash_type"] = "success"
    return response


@router.get("/{p_id}")
def get_project_by_id(
    request: Request,
    p_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access_only_view),
):
    all_users = admin_service.get_all_users(db)
    available_users = project_service.get_available_users(db, p_id, all_users)
    tasks, task_count = project_service.get_project_tasks(db, p_id, "", "", "", "", "", "")
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")

    activities = project_service.get_activities(db, project)
    return templates.TemplateResponse(
        request,
        "projects/detail.html",
        {
            "user": user,
            "tasks": tasks,
            "project": project,
            "members": admin_service.get_all_users(db),
            "available_users": available_users,
            "flash_type": flash_type,
            "flash_message": flash_message,
            "activities": activities,
        },
    )


@router.get("/{p_id}/edit")
def edit_project_page(
    p_id: int,
    request: Request,
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access),
):
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    return templates.TemplateResponse(
        request, "projects/edit.html", {"user": user, "field_errors": None, "project": project}
    )


@router.post("/{p_id}/edit")
def edit_project(
    request: Request,
    p_id: int,
    user: User = Depends(require_user),
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    project: Project = Depends(get_project_with_access),
):
    name = name.lower()
    description = description.lower()
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    try:
        form = ProjectForm(name=name, description=description)
    except ValidationError as e:
        field_errors = {}
        for error in e.errors():
            field = error["loc"][0]
            message = error["msg"]
            field_errors.setdefault(field, []).append(message)
        return templates.TemplateResponse(
            request,
            "projects/edit.html",
            {"user": user, "name": name, "description": description, "field_errors": field_errors},
        )
    project_service.edit_project(db, project, form)
    log_activity(
        db,
        project.id,
        user.id,
        "updated",
        "project",
        project.id,
        f"Проект был изменён. Имя: «{project.name}», Описание: {project.description}",
    )
    request.session["flash_message"] = "Проект изменён!"
    request.session["flash_type"] = "success"

    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response


@router.post("/{p_id}/delete")
def delete_project(
    request: Request,
    p_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    project: Project = Depends(get_project_with_access),
):
    if not permission_service.can_delete_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    project_service.delete_project(db, project)
    request.session["flash_message"] = "Проект удалён! :("
    request.session["flash_type"] = "success"
    response = RedirectResponse("/projects", status_code=303)
    return response


@router.post("/{p_id}/members")
def manage_member(
    request: Request,
    p_id: int,
    member_id: int = Form(...),
    role: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    action: str = Form(""),
    project: Project = Depends(get_project_with_access),
):
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    if action == "add":
        form = MemberForm(member_id=member_id, role=role)
        project_service.add_member(db, project, form)
        log_activity(
            db,
            project.id,
            user.id,
            "member_added",
            "user",
            member_id,
            f"Пользователь {db.get(User, member_id).display_name} добавлен в проект",
        )
        request.session["flash_message"] = "В проекте на 1 участника больше!"
        request.session["flash_type"] = "success"
    elif action == "remove":
        form = DeleteForm(member_id=member_id, project_id=project.id)
        project_service.delete_member(db, form)
        log_activity(
            db,
            project.id,
            user.id,
            "member_deleted",
            "user",
            member_id,
            f"Пользователь {db.get(User, member_id).display_name} удалён из проекта",
        )
        request.session["flash_message"] = "В проекте на 1 участника меньше!"
        request.session["flash_type"] = "success"
    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response


@router.get("/{p_id}/tasks")
def get_project_tasks(
    request: Request,
    p_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access_only_view),
    status: str = Query(""),
    priority: str = Query(""),
    sort_by: str = Query("created_at"),
    filter_member: str = Query(""),
    sort_order: str = Query("desc"),
    search: str = Query(""),
):
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")
    filters = {
        "status": status,
        "priority": priority,
        "filter_member": filter_member,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "search": search,
    }
    request.session[f"filters_{p_id}"] = filters
    tasks, total_count = project_service.get_project_tasks(
        db, p_id, status, priority, filter_member, sort_order, sort_by, search
    )
    tasks_by_status = {
        "Новая": [],
        "В работе": [],
        "Выполнена": [],
    }

    for task in tasks:
        status_name = task.status.value
        if status_name in tasks_by_status:
            tasks_by_status[status_name].append(task)
    return templates.TemplateResponse(
        request,
        "projects/project_tasks.html",
        {
            "user": user,
            "today": date.today(),
            "tasks": tasks,
            "project": project,
            "status": status,
            "priority": priority,
            "filter_member": filter_member,
            "search": search,
            "total_count": total_count,
            "priorities": Priority,
            "statuses": Status,
            "tasks_by_status": tasks_by_status,
            "flash_message": flash_message,
            "flash_type": flash_type,
        },
    )


@router.get("/{p_id}/tasks/create")
def create_task_page(
    request: Request,
    p_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access),
):
    return templates.TemplateResponse(
        request,
        "tasks/create.html",
        {
            "user": user,
            "project": project,
            "field_errors": None,
            "members": project_service.get_project_members(db, project),
            "statuses": Status,
            "priorities": Priority,
        },
    )


@router.post("/{p_id}/tasks/create")
def create_task(
    request: Request,
    p_id: int,
    title: str = Form(...),
    description: str = Form(""),
    status: Status = Form(default=Status.IN_WORK),
    priority: Priority = Form(default=Priority.MEDIUM),
    assignee_id: str = Form(""),
    due_date: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    project: Project = Depends(get_project_with_access),
):
    title = title.lower()
    description = description.lower()
    assignee_id = int(assignee_id) if assignee_id else None
    due_date = date.fromisoformat(due_date) if due_date else None
    if project is None:
        raise HTTPException(404, "Проект не найден")
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
        fields_errors = {}
        for error in e.errors():
            field = error["loc"][0]
            message = error["msg"]
            fields_errors.setdefault(field, []).append(message)
        return templates.TemplateResponse(
            request,
            "tasks/create.html",
            {
                "user": user,
                "project": project,
                "field_errors": fields_errors,
                "title": title,
                "description": description,
                "due_date": due_date,
                "status": status,
                "priority": priority,
                "assignee_id": assignee_id,
                "members": project_service.get_project_members(db, project),
                "statuses": Status,
                "priorities": Priority,
            },
        )
    task = task_service.create_task(db, user, p_id, form)
    log_activity(
        db,
        p_id,
        user.id,
        "created",
        "task",
        task.id,
        f"создал задачу «{task.title}». Название: {title},  Статус: {status}, Приоритет: {priority},"
        f" Назначенный: {db.get(User, assignee_id).display_name}, Выполнить до: {due_date}",
    )
    request.session["flash_message"] = "Задача создана!"
    request.session["flash_type"] = "success"
    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response


@router.get("{p_id}/tasks/export")
def export_tasks_csv(
    p_id: int,
    request: Request,
    status: str = Query(""),
    priority: str = Query(""),
    filter_member: str = Query(""),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    search: str = Query(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project=Depends(get_project_with_access),
):
    if not project:
        raise HTTPException(404, "Проект не найден")

    tasks, task_count = project_service.get_project_tasks(
        db, p_id, status, priority, filter_member, sort_order, sort_by, search
    )

    # Генерируем CSV
    output = io.StringIO()
    # UTF-8 BOM для корректного открытия в Excel
    output.write("\ufeff")

    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Заголовки
    writer.writerow(
        [
            "ID",
            "Название",
            "Описание",
            "Статус",
            "Приоритет",
            "Исполнитель",
            "Создатель",
            "Дата создания",
            "Срок выполнения",
            "Дата обновления",
        ]
    )

    # Данные
    for task in tasks:
        writer.writerow(
            [
                task.id,
                task.title,
                task.description or "",
                task.status.value if hasattr(task.status, "value") else str(task.status),
                task.priority.value if hasattr(task.priority, "value") else str(task.priority),
                task.assignee.username if task.assignee else "",
                task.user.username if task.user else "",
                task.created_at.strftime("%d.%m.%Y %H:%M") if task.created_at else "",
                task.due_date.strftime("%d.%m.%Y") if task.due_date else "",
                task.updated_at.strftime("%d.%m.%Y %H:%M") if task.updated_at else "",
            ]
        )

    date_str = datetime.now().strftime("%Y%m%d_%H%M")

    safe_name = "".join(c for c in project.name if c.isalnum() or c in (" ", "_", "-")).strip()
    raw_filename = f"tasks_{safe_name}_{date_str}.csv"

    encoded_filename = urllib.parse.quote(raw_filename)

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
