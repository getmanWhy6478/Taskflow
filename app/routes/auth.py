from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, Query, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.forms.login import LoginForm
from app.forms.register import RegisterForm
from app.models.users import User
from app.services import auth_services as auth_services
from app.services import search_services as search_service
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
    auth_services.add_user(form, db, hashed_password)
    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request, next_page: str = Query(""), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        user = db.get(User, user_id)
        if user and not user.is_banned and next_page and next_page.startswith("/"):
            return RedirectResponse(unquote(next_page), status_code=303)
    return templates.TemplateResponse(
        request, "auth/login.html", {"user": None, "next_page": next_page}
    )


@router.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    next_page: str = Form(""),
):
    form = LoginForm(username=username, password=password)
    user = search_service.search_user_by_username(db, form.username)
    if not user or not auth_services.verify_password(form.password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "user": None,
                "error": "No user with that username exists or incorrect password.",
                "next_page": next_page,
            },
            status_code=401,
        )
    if user.is_banned:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "error": "Ваш аккаунт заблокирован. Обратитесь к администратору.",
                "username": username,
            },
            status_code=403,
        )
    request.session["user_id"] = user.id
    if next_page:
        decoded_next = unquote(next_page)
        if decoded_next.startswith("/") and not decoded_next.startswith("//"):
            return RedirectResponse(decoded_next, status_code=303)
    response = RedirectResponse(next_page or "/dashboard", status_code=303)
    return response


@router.post("/logout")
def logout(request: Request):
    response = RedirectResponse("/login", status_code=303)
    request.session.clear()
    return response


@router.get("/blocked_page")
def blocked_page(request: Request):
    return templates.TemplateResponse(request, "auth/blocked.html", {"user": None})
