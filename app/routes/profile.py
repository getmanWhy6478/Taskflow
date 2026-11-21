from fastapi import APIRouter, Depends, Form
from pydantic import ValidationError
from sqlalchemy.orm.session import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.database import get_db
from app.dependencies import require_user, validate_csrf_token
from app.forms.change_form import ChangeUser
from app.forms.change_password_form import ChangePassword
from app.main import CsrfProtect
from app.models import User
from app.services import auth_services, profile_services
from app.templates.templates import templates

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
def profile(
    request: Request, user: User = Depends(require_user), csrf_protect: CsrfProtect = Depends()
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    flash_message = request.session.pop("flash_message", None)
    flash_type = request.session.pop("flash_type", "success")
    response = templates.TemplateResponse(
        request,
        "profile.html",
        {
            "user": user,
            "password_errors": None,
            "field_errors": None,
            "flash_type": flash_type,
            "flash_message": flash_message,
            "csrf_token": csrf_token,
        },
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("")
def change_name_or_password(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    new_password: str = Form(""),
    new_name: str = Form(""),
    action=Form(...),
    confirm_password: str = Form(""),
    current_password=Form(""),
    _: None = Depends(validate_csrf_token),
    csrf_protect: CsrfProtect = Depends(),
):
    if action == "change_name":
        try:
            form = ChangeUser(username=new_name)
        except ValidationError as e:
            field_errors = {}
            for error in e.errors():
                field = error["loc"][0]
                message = error["msg"]
                field_errors.setdefault(field, []).append(message)
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            response = templates.TemplateResponse(
                request,
                "profile.html",
                {
                    "user": user,
                    "field_errors": field_errors,
                    "new_name": new_name,
                    "csrf_token": csrf_token,
                },
            )
            csrf_protect.set_csrf_cookie(signed_token, response)
            return response
        profile_services.change_name(db, user, form)
        request.session["flash_message"] = "Имя успешно изменено"
        request.session["flash_type"] = "success"
        return RedirectResponse(url="/profile", status_code=303)

    elif action == "change_password":
        password_errors = {}
        if not current_password or not new_password or not confirm_password:
            password_errors["general"] = "Все поля пароля обязательны для заполнения"

        elif new_password != confirm_password:
            password_errors["confirm_password"] = "Пароли не совпадают"

        elif not auth_services.verify_password(current_password, user.password_hash):
            password_errors["current_password"] = "Неверный текущий пароль"

        if password_errors:
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            response = templates.TemplateResponse(
                request,
                "profile.html",
                {
                    "user": user,
                    "password_errors": password_errors,
                    "new_name": new_name,
                    "csrf_token": csrf_token,
                },
            )
            csrf_protect.set_csrf_cookie(signed_token, response)
            return response
        try:
            form = ChangePassword(password=new_password)
        except ValidationError as e:
            field_errors = {}
            for error in e.errors():
                field = error["loc"][0]
                message = error["msg"]
                field_errors.setdefault(field, []).append(message)
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            response = templates.TemplateResponse(
                request,
                "profile.html",
                {
                    "user": user,
                    "field_errors": field_errors,
                    "new_name": new_name,
                    "csrf_token": csrf_token,
                },
            )
            csrf_protect.set_csrf_cookie(signed_token, response)
            return response
        profile_services.change_password(db, user, form)
        request.session["flash_message"] = "Пароль успешно изменён"
        request.session["flash_type"] = "success"
        return RedirectResponse(url="/profile", status_code=303)
    return RedirectResponse(url="/profile", status_code=303)
