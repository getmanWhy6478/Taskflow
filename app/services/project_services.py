from datetime import datetime

from sqlalchemy import asc, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.forms.delete import DeleteForm
from app.forms.member import MemberForm
from app.forms.project import ProjectForm
from app.models import Priority, Project, ProjectsMember, Task, User


def create_project(db: Session, form: ProjectForm, user: User) -> Project:
    project = Project(name=form.name, description=form.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


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


def add_member(db: Session, project: Project, form: MemberForm) -> None:
    project_member = ProjectsMember(user_id=form.member_id, project_id=project.id, role=form.role)
    db.add(project_member)
    db.commit()
    db.refresh(project_member)
    return


def get_all_projects(db: Session, user: User) -> list[Project]:
    found = select(Project).where(
        or_(Project.owner_id == user.id, Project.members.any(User.id == user.id))
    )
    return list(db.scalars(found))


def get_project_by_id(db: Session, p_id: int) -> Project:
    found = select(Project).where(Project.id == p_id)
    return db.scalar(found)


def get_project_members(db: Session, project: Project) -> list[User]:
    return list(project.members)


def get_project_tasks(
    db: Session,
    p_id: int,
    status: str,
    priority: str,
    filter_member: str,
    order: str,
    sort_by: str,
    search: str,
    page: int,
    per_page: int | None = None,
) -> tuple[list[Task], int]:
    found = select(Task).where(Task.project_id == p_id)

    if status != "":
        found = found.where(Task.status == status)

    if priority != "":
        found = found.where(Task.priority == priority)

    if filter_member != "":
        found = found.where(Task.assignee_id == int(filter_member))

    enum_orders = {
        "priority": case(
            (Task.priority == Priority.LOW, 1),
            (Task.priority == Priority.MEDIUM, 2),
            (Task.priority == Priority.HIGH, 3),
            else_=0,
        )
    }

    if search != "":
        search = search.lower()
        found = found.where(
            or_(Task.title.like(f"%{search}%"), Task.description.like(f"%{search}%"))
        )

    column = enum_orders[sort_by] if sort_by in enum_orders else getattr(Task, sort_by, None)

    if column is not None:
        found = found.order_by(asc(column)) if order == "asc" else found.order_by(desc(column))
    else:
        found = found.order_by(desc(Task.created_at))

    total_count = select(func.count()).select_from(found.subquery())

    total_count = db.scalar(total_count) or 0

    if per_page:
        offset = (page - 1) * per_page
        found = found.limit(per_page).offset(offset)

    return list(db.scalars(found)), total_count


def get_available_users(db: Session, p_id: int, users: list[User]) -> list[User]:
    member_ids = set(
        db.scalars(select(ProjectsMember.user_id).where(ProjectsMember.project_id == p_id))
    )
    users_not_in_project = [u for u in users if u.id not in member_ids]
    return users_not_in_project


def delete_member(db: Session, form: DeleteForm) -> None:
    project_member = db.scalar(
        select(ProjectsMember).where(
            ProjectsMember.user_id == form.member_id, ProjectsMember.project_id == form.project_id
        )
    )
    db.delete(project_member)
    db.commit()
    return
