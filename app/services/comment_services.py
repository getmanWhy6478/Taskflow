from sqlalchemy.orm import Session

from app.forms.comment import CommentForm
from app.models.comments import Comment
from app.models.tasks import Task
from app.models.users import User


def create_comment(db: Session, form: CommentForm, task: Task, user: User) -> None:
    new_comment = Comment(body=form.text, task_id=task.id, user_id=user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return


def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()
    db.refresh(comment)
