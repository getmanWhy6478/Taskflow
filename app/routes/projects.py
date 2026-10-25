from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user
from app.forms.project import ProjectForm
from app.forms.tasks import TaskForm
from app.models.priority import Priority
from app.models.projects import Project
from app.models.status import Status
from app.models.users import User
from app.services import permission_services as permission_service
from app.services import project_services as project_service
from app.services import task_services as task_service
from app.templates.templates import templates

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def get_projects(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    projects = project_service.get_all_projects(db)
    return templates.TemplateResponse(
        request,
        "projects/list.html",
        {"user": user, "projects": projects},
    )


@router.get("/create")
def create_project_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "projects/list.html", {"user": user})


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
        project_service.create_project(db, form, user)
        response = RedirectResponse("/projects", status_code=303)
        return response
    except ValueError:
        return templates.TemplateResponse(request, "projects/list.html", {"user": user})


@router.get("/{p_id}")
def get_project_by_id(
    request: Request, p_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    project = project_service.get_project_by_id(db, p_id)

    return templates.TemplateResponse(
        request,
        "projects/detail.html",
        {
            "user": user,
            "project": project
        },
    )


@router.get("/{id}/edit")
def edit_project_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "project_edit.html", {"user": user})


@router.post("/{p_id}/edit")
def edit_project(
    request: Request,
    p_id: int,
    user: User = Depends(require_user),
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    project = project_service.get_project_by_id(db, p_id)
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    try:
        form = ProjectForm(name=name, description=description)
        project_service.edit_project(db, project, form)
        response = RedirectResponse("/projects")
        return response
    except ValueError:
        return templates.TemplateResponse(request, "project_create.html", {"user": user})


@router.post("/{p_id}/delete")
def delete_project(
    request: Request, p_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    project = project_service.get_project_by_id(db, p_id)
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    project_service.delete_project(db, project)
    response = RedirectResponse("/projects")
    return response


@router.post("/{p_id}/members")
def add_member(
    request: Request,
    role: str,
    p_id: int,
    member_id: int,
    db=Depends(get_db),
    user: User = Depends(require_user),
):
    project = project_service.get_project_by_id(db, p_id)
    member = db.get(User, member_id)
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(status_code=403, detail="Нет прав")
    project_service.add_member(db, project, member, role)
    response = RedirectResponse("/projects")
    return response


@router.get("/{p_id}/tasks")
def get_project_tasks(
    request: Request, p_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    tasks = project_service.get_project_tasks(db, p_id)
    return templates.TemplateResponse(
        request,
        "projects/tasks.html",
        {"user": user, "tasks": tasks},
    )


@router.get("/{id}/tasks/{task_id}/create")
def create_task_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "task_create.html", {"user": user})


@router.post("/{p_id}/tasks/create")
def create_task(
    request: Request,
    p_id: int,
    title: str = Form(...),
    description: str = Form(...),
    status: Status = Form(...),
    priority: Priority = Form(default=Priority.MEDIUM),
    assignee_id: int | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    project = db.get(Project, p_id)
    if project is None:
        raise HTTPException(404, "Проект не найден")
    if not permission_service.can_edit_project(user, project):
        raise HTTPException(403, "Нет прав")
    try:
        form = TaskForm(
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
        )
        task_service.create_task(db, user, p_id, form)
        response = RedirectResponse("/projects", status_code=303)
        return response

    except ValueError:
        return templates.TemplateResponse(request, "task_create.html", {"user": user})
