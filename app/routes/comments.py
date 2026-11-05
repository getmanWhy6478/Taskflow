from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import delete_comment_with_access, require_user
from app.models.users import User
from app.services import comment_services as comment_service

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/{c_id}/delete")
def delete_comment(
    c_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    comment=Depends(delete_comment_with_access),
):
    comment_service.delete_comment(db, comment)
    response = RedirectResponse("/projects", status_code=303)
    return response
