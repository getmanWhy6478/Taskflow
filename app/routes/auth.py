from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.forms.login import LoginForm
from app.forms.register import RegisterForm
from app.models.users import User
from app.services import auth_services
from app.services.auth_services import hash_password
from app.templates.templates import templates

router = APIRouter(tags=["auth"])


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"user": None})


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
        if db.query(User).filter_by(username=form.username).first():
            return templates.TemplateResponse(
                request,
                "register.html",
                {"user": None, "error": "Username already in use."},
                status_code=400,
            )
        hashed_password = hash_password(form.password)
        user = User(
            username=form.username,
            password_hash=hashed_password,
            email=form.email,
            display_name=form.display_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return RedirectResponse("/login", status_code=303)
    except ValueError:
        return templates.TemplateResponse(request, "register.html", {"user": None}, status_code=400)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None})


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
            "login.html",
            {"user": None, "error": "No user with that username exists or incorrect password."},
            status_code=401,
        )
    response = RedirectResponse("/projects", status_code=303)
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
