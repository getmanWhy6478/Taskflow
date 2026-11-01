from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Task
from app.models.users import User


def get_stats(db: Session, user: User) -> dict:
    tasks_count_new = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.assignee_id == user.id, Task.status == "NEW")
    )
    tasks_count_in_work = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.assignee_id == user.id, Task.status == "IN_WORK")
    )
    tasks_count_week_complete = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.assignee_id == user.id,
            Task.status == "COMPLETE",
            datetime.now() - Task.updated_at < timedelta(days=7),
        )
    )
    tasks_count_wasted = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.assignee_id == user.id, Task.status != "COMPLETE", datetime.today() > Task.due_date
        )
    )
    stats = {
        "new_tasks_count": tasks_count_new,
        "in_work_tasks_count": tasks_count_in_work,
        "week_complete_tasks_count": tasks_count_week_complete,
        "wasted_tasks_count": tasks_count_wasted,
    }
    return stats
