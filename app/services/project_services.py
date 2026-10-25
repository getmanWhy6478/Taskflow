from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.forms.project import ProjectForm
from app.models import ProjectsMember
from app.models.projects import Project
from app.models.tasks import Task
from app.models.users import User


def create_project(db: Session, form: ProjectForm, user: User) -> None:
    project = Project(name=form.name, description=form.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return


def edit_project(db: Session, project: Project, form: ProjectForm) -> None:
    project.name = form.name
    project.description = form.description
    project.updated_at = datetime.now()
    db.add(project)
    db.commit()
    db.refresh(project)
    return


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
    return


def add_member(db: Session, project: Project, member: User, role: str) -> None:
    project_member = ProjectsMember(user_id=member.id, project_id=project.id, role=role)
    db.add(project_member)
    db.commit()
    db.refresh(project_member)
    return


def get_all_projects(db: Session) -> list[Project]:
    found = select(Project)
    return list(db.scalars(found))


def get_project_by_id(db: Session, p_id: int) -> Project:
    found = select(Project).where(Project.id == p_id)
    return db.scalar(found)


def get_project_tasks(db: Session, p_id: int) -> list[Task]:
    found = select(Task).where(Task.project_id == p_id)
    return list(db.scalars(found))
