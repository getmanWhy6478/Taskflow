from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_admin, validate_csrf_token
from app.main import CsrfProtect
from app.models.users import User
from app.services import admin_services as admin_service
from app.templates.templates import templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_users(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    users = admin_service.get_all_users(db)
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")
    tasks_count = admin_service.get_user_tasks(db)
    response = templates.TemplateResponse(
        request,
        "admin.html",
        {
            "user": user,
            "users": users,
            "flash_type": flash_type,
            "flash_message": flash_message,
            "tasks_count": tasks_count,
            "csrf_token": csrf_token,
        },
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/users/{u_id}/toggle-active")
def ban_user(
    request: Request,
    u_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    _: None = Depends(validate_csrf_token),
):
    user_changed = db.get(User, u_id)
    if u_id == user.id:
        raise HTTPException(400, "Нельзя заблокировать самого себя")
    admin_service.ban_user(db, user_changed)
    request.session["flash_message"] = "Пользователь успешно забанен!"
    request.session["flash_type"] = "success"
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{u_id}/toggle-active/unblock")
def unban_user(
    request: Request,
    u_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    _: None = Depends(validate_csrf_token),
):
    user_changed = db.get(User, u_id)
    if u_id == user.id:
        raise HTTPException(400, "Нельзя заблокировать самого себя")
    admin_service.unban_user(db, user_changed)
    request.session["flash_message"] = "Пользователь успешно разбанен!"
    request.session["flash_type"] = "success"
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{u_id}/toggle-admin")
def make_user_admin(
    request: Request,
    u_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    action: str = Form(...),
    _: None = Depends(validate_csrf_token),
):
    user_changed = db.get(User, u_id)
    if u_id == user.id:
        raise HTTPException(400, "Нельзя заблокировать самого себя")
    if action == "make_admin":
        request.session["flash_message"] = "Пользователь теперь имеет права администратора!"
        request.session["flash_type"] = "success"
        admin_service.admin_user(db, user_changed)
    else:
        request.session["flash_message"] = "Пользователь теперь не имеет прав администратора!"
        request.session["flash_type"] = "success"
        admin_service.unadmin_user(db, user_changed)
    return RedirectResponse(url="/admin/users", status_code=303)
