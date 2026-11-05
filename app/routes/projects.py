from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import get_project_with_access, require_user
from app.forms.delete import DeleteForm
from app.forms.member import MemberForm
from app.forms.project import ProjectForm
from app.forms.tasks import TaskForm
from app.models import Priority, Project, Status, User
from app.services import admin_services as admin_service
from app.services import permission_services as permission_service
from app.services import project_services as project_service
from app.services import task_services as task_service
from app.templates.templates import templates

router = APIRouter(prefix="/projects", tags=["projects"])

TASKS_PER_PAGE = 10


@router.get("")
def get_projects(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    projects = project_service.get_all_projects(db, user)
    return templates.TemplateResponse(
        request,
        "projects/list.html",
        {"user": user, "projects": projects},
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
    description: str = Form(...),
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
    return response


@router.get("/{p_id}")
def get_project_by_id(
    request: Request,
    p_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    status: str = Query(""),
    priority: str = Query(""),
    sort_by: str = Query("created_at"),
    filter_member: str = Query(""),
    sort_order: str = Query("desc"),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    project: Project = Depends(get_project_with_access),
):
    all_users = admin_service.get_all_users(db)
    available_users = project_service.get_available_users(db, p_id, all_users)

    tasks, total_count = project_service.get_project_tasks(
        db, p_id, status, priority, filter_member, sort_order, sort_by, search, page, TASKS_PER_PAGE
    )

    total_pages = max(1, (total_count + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE)

    if page > total_pages:
        page = total_pages
        return RedirectResponse(
            f"projects/{p_id}",
            status_code=303,
        )

    return templates.TemplateResponse(
        request,
        "projects/detail.html",
        {
            "today": date.today(),
            "user": user,
            "project": project,
            "tasks": tasks,
            "members": admin_service.get_all_users(db),
            "priorities": Priority,
            "statuses": Status,
            "available_users": available_users,
            "status": status,
            "priority": priority,
            "filter_member": filter_member,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "tasks_per_page": TASKS_PER_PAGE,
        },
    )


@router.get("/{p_id}/edit")
def edit_project_page(
    p_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access),
):
    return templates.TemplateResponse(
        request, "projects/edit.html", {"user": user, "field_errors": None, "project": project}
    )


@router.post("/{p_id}/edit")
def edit_project(
    request: Request,
    p_id: int,
    user: User = Depends(require_user),
    name: str = Form(...),
    description: str = Form(...),
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
    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response


@router.post("/{p_id}/delete")
def delete_project(
    p_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    project: Project = Depends(get_project_with_access),
):
    if not permission_service.can_delete_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    project_service.delete_project(db, project)
    response = RedirectResponse("/projects", status_code=303)
    return response


@router.post("/{p_id}/members")
def manage_member(
    p_id: int,
    member_id: int = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    action: str = Query(""),
    project: Project = Depends(get_project_with_access),
):
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    if action == "add":
        form = MemberForm(member_id=member_id, role=role)
        project_service.add_member(db, project, form)
    elif action == "remove":
        form = DeleteForm(member_id=member_id, project_id=project.id)
        project_service.delete_member(db, project, form)
    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response


@router.get("/{p_id}/tasks")
def get_project_tasks(
    request: Request,
    p_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    project: Project = Depends(get_project_with_access),
):
    tasks = project_service.get_project_tasks(db, p_id, "", "", "", "", "")
    return templates.TemplateResponse(
        request,
        "projects/tasks.html",
        {"user": user, "tasks": tasks, "project": project},
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
    task_service.create_task(db, user, p_id, form)
    response = RedirectResponse(f"/projects/{p_id}", status_code=303)
    return response
