from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import delete_comment_with_access, require_user
from app.models import Comment, User
from app.services import comment_services as comment_service

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/{c_id}/delete")
def delete_comment(
    request: Request,
    c_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    comment: Comment = Depends(delete_comment_with_access),
):
    comment_service.delete_comment(db, comment)
    request.session["flash_message"] = "Комментарий удалён"
    request.session["flash_type"] = "success"
    response = RedirectResponse("/projects", status_code=303)
    return response
