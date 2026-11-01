from fastapi import APIRouter, Depends, Form, Request, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.forms.login import LoginForm
from app.forms.register import RegisterForm
from app.models.users import User
from app.services import auth_services as auth_services
from app.services.auth_services import hash_password
from app.templates.templates import templates

router = APIRouter(tags=["auth"])


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request, "auth/register.html", {"user": None, "field_errors": None}
    )


@router.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        form = RegisterForm(
            username=username, email=email, password=password, display_name=display_name
        )
    except ValidationError as e:
        field_errors = {}
        for error in e.errors():
            field = error["loc"][0]
            message = error["msg"]
            field_errors.setdefault(field, []).append(message)
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "user": None,
                "field_errors": field_errors,
                "username": username,
                "email": email,
                "display_name": display_name,
            },
            status_code=400,
        )
    if auth_services.is_user_already_registered(db, form):
        errors = []
        errors.append("Username already in use.")
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"user": None, "errors": errors, "field_errors": None},
            status_code=400,
        )
    hashed_password = hash_password(form.password)
    auth_services.add_user(form, db,  hashed_password)
    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {"user": None})


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    form = LoginForm(username=username, password=password)
    user = db.query(User).filter_by(username=form.username).first()
    if not user or not auth_services.verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"user": None, "error": "No user with that username exists or incorrect password."},
            status_code=401,
        )
    if user.is_banned:
        return templates.TemplateResponse(
            request, "auth/login.html",
            {
                "error": "Ваш аккаунт заблокирован. Обратитесь к администратору.",
                "username": username
            },
            status_code=403,
        )
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        "session",
        auth_services.create_session_token(user.id),
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("session")
    return response

@router.get("/blocked_page")
def blocked_page(request: Request):
    return templates.TemplateResponse(
        request, "auth/blocked.html", {"user": None}
    )
