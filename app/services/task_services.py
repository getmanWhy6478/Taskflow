from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.forms.tasks import TaskForm
from app.models import Task, User, Status, Comment


def create_task(db: Session, user: User, p_id: int, form: TaskForm) -> None:
    task = Task(
        title=form.title,
        description=form.description,
        status=form.status,
        priority=form.priority,
        assignee_id=form.assignee_id,
        project_id=p_id,
        author_id=user.id,
        due_date=form.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return


def update_task(db: Session, task: Task, form: TaskForm) -> None:
    task.title = form.title
    task.description = form.description
    task.status = form.status
    task.priority = form.priority
    task.assignee_id = form.assignee_id
    task.due_date = form.due_date
    task.updated_at = datetime.now()
    db.add(task)
    db.commit()
    db.refresh(task)
    return


def update_task_status(db: Session, task: Task, status: Status) -> None:
    task.status = status
    task.updated_at = datetime.now()
    db.add(task)
    db.commit()
    db.refresh(task)
    return


def get_task_by_id(db: Session, t_id: int) -> Task:
    task = select(Task).where(Task.id == t_id)
    return db.scalar(task)


def get_task_by_comment(db: Session, comment: Comment) -> Task:
    task = select(Task).where(comment_id=comment.id)
    return db.scalar(task)


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
    return

def get_recent_tasks(db: Session, user: User, limit: int) -> List[Task]:
    tasks = select(Task).where(Task.assignee_id == user.id).order_by(Task.created_at).limit(limit)
    return list(db.scalars(tasks))

def get_users_tasks(db: Session, user: User) -> List[Task]:
    tasks = select(Task).where(Task.assignee_id == user.id)
    return list(db.scalars(tasks))

def get_tasks_comments(db: Session, task: Task) -> List[Comment]:
    comments = select(Comment).where(Comment.task_id == task.id)
    return list(db.scalars(comments))

