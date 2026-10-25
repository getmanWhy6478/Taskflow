from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user
from app.models.users import User
from app.services import admin_services as admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_users(db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.is_admin:
        users = admin_service.get_all_users(db)
        return RedirectResponse(url="/admin/users")
    else:
        return RedirectResponse(url="/admin/users")


@router.post("/users/{u_id}/toggle-active")
def ban_user(u_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.is_admin:
        user = db.get(User, u_id)
        admin_service.ban_user(db, user)
        return RedirectResponse(url="/admin/users")
    else:
        return RedirectResponse(url="/admin/users")


@router.post("/users/{u_id}/toggle-admin")
def make_user_admin(u_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if user.is_admin:
        user = db.get(User, u_id)
        admin_service.admin_user(db, user)
        return RedirectResponse(url="/admin/users")
    else:
        return RedirectResponse(url="/admin/users")
