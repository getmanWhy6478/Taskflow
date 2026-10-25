from app.models import Comment, Project, Task, User


def can_edit_project(user: User, project: Project) -> bool:
    return user.is_admin or project.owner_id == user.id


def can_edit_task(user: User, task: Task) -> bool:
    return user.is_admin or task.project.owner_id == user.id


def can_delete_comment(user: User, comment: Comment) -> bool:
    return comment.author_id == user.id


def is_admin(user: User) -> bool:
    return user.is_admin
