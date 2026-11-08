from app.models import Comment, Project, Task, User


def can_edit_project(user: User, project: Project) -> bool:
    return project.owner_id == user.id


def can_edit_task(user: User, task: Task) -> bool:
    return task.project.owner_id == user.id or task.author_id == user.id or user.is_admin


def can_edit_task_status(user: User, task: Task) -> bool:
    return (
        task.project.owner_id == user.id or task.author_id == user.id or task.assignee_id == user.id
    )


def can_delete_comment(user: User, comment: Comment) -> bool:
    return comment.author_id == user.id or user.is_admin


def can_delete_project(user: User, project: Project) -> bool:
    return project.owner_id == user.id


def can_delete_task(user: User, task: Task) -> bool:
    return task.project.owner_id == user.id or task.author_id == user.id
