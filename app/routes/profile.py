from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm.session import Session
from starlette.requests import Request

from pydantic import ValidationError

from app.dependencies import require_user
from app.services import profile_services, auth_services
from app.templates.templates import templates

from app.forms.change_form import ChangeUser
from app.forms.change_password_form import ChangePassword

from starlette.responses import RedirectResponse


from app.database import get_db

from app.models import User

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("")
def profile(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "profile.html", {"user": user, "password_errors": None, "field_errors": None})

@router.post("")
def change_name_or_password(request: Request, db:Session = Depends(get_db),
                            user: User = Depends(require_user), new_password: str = Form(""),
                            new_name: str = Form(""), action = Form(...), confirm_password:str = Form(""),
                            current_password = Form("")):
    if action == "change_name":
        try:
            form = ChangeUser(username=new_name)
        except ValidationError as e:
            field_errors = {}
            for error in e.errors():
                field = error["loc"][0]
                message = error["msg"]
                field_errors.setdefault(field, []).append(message)
            return templates.TemplateResponse(
                request, "profile.html",
                {"user": user, "field_errors": field_errors, "new_name": new_name}
            )
        profile_services.change_name(db, user, form)
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
            return templates.TemplateResponse(
                request, "profile.html",
                {"user": user, "password_errors": password_errors, "new_name": new_name}
            )
        try:
            form = ChangePassword(password=new_password)
        except ValidationError as e:
            field_errors = {}
            for error in e.errors():
                field = error["loc"][0]
                message = error["msg"]
                field_errors.setdefault(field, []).append(message)
            return templates.TemplateResponse(
                request, "profile.html",
                {"user": user, "field_errors": field_errors, "new_name": new_name}
            )
        profile_services.change_password(db, user, form)
        return RedirectResponse(url="/profile", status_code=303)
    return RedirectResponse(url="/profile", status_code=303)

