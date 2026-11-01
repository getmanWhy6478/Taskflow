from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.requests import Request

from app.templates.templates import templates

from app.database import get_db
from app.dependencies import require_admin
from app.models.users import User
from app.services import admin_services as admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_users(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = admin_service.get_all_users(db)
    return templates.TemplateResponse(
        request,
            "admin.html",
            {
                "user": user,
                "users": users,
            },
        )


@router.post("/users/{u_id}/toggle-active")
def ban_user(u_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    user_changed = db.get(User, u_id)
    if u_id == user.id:
        raise HTTPException(400, "Нельзя заблокировать самого себя")
    admin_service.ban_user(db, user_changed)
    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/users/{u_id}/toggle-active/unblock")
def unban_user(u_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if user.is_admin:
        user_changed = db.get(User, u_id)
        admin_service.unban_user(db, user_changed)
        return RedirectResponse(url="/admin/users", status_code=303)
    else:
        return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{u_id}/toggle-admin")
def make_user_admin(u_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin), action: str = Form(...)):
    user_changed = db.get(User, u_id)
    if u_id == user.id:
        raise HTTPException(400, "Нельзя заблокировать самого себя")
    if action == "make_admin":
        admin_service.admin_user(db, user_changed)
    else:
        admin_service.unadmin_user(db, user_changed)
    return RedirectResponse(url="/admin/users", status_code=303)
