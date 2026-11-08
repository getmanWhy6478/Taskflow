from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_user
from app.models.users import User
from app.services import stats_service
from app.services import task_services as task_service
from app.templates.templates import templates

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)):
    stats = stats_service.get_stats(db, user)
    recent_tasks = task_service.get_recent_tasks(db, user, limit=5)
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "stats": stats,
            "recent_tasks": recent_tasks,
            "flash_type": flash_type,
            "flash_message": flash_message,
        },
    )
