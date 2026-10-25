from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user
from app.models import Comment
from app.models.users import User
from app.services import comment_services as comment_service
from app.services import permission_services as permission_service

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("{c_id}/delete")
def delete_comment(c_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    comment = db.get(Comment, c_id)
    if permission_service.can_delete_comment(user, comment):
        comment_service.delete_comment(db, comment)
        response = RedirectResponse("/projects")
        return response
    return RedirectResponse("/users")
