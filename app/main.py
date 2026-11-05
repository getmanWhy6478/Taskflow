from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.dependencies import AuthRequiredException

from app.config import settings

from starlette.requests import Request

from starlette.exceptions import HTTPException

from app.database import Base, engine
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.comments import router as comment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.profile import router as profile_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from app.templates.templates import templates

app = FastAPI(title="TaskFlow")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=14 * 24 * 60 * 60,
    same_site="lax",
)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(admin_router)
app.include_router(comment_router)
app.include_router(dashboard_router)
app.include_router(profile_router)


@app.get("/")
def index():
    return RedirectResponse("/dashboard", status_code=303)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    if exc.status_code == 404:
        return templates.TemplateResponse(
            request,
            "errors/404.html",
            {
                "user": request.session.get("user"),
                "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            },
            status_code=404,
        )
    elif exc.status_code == 403:
        return templates.TemplateResponse(
            request,
            "errors/403.html",
            {
                "user": request.session.get("user"),
                "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            },
            status_code=403,
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/404.html",
            {
                "user": request.session.get("user"),
                "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            },
            status_code=exc.status_code,
        )

@app.exception_handler(AuthRequiredException)
async def auth_required_handler(request: Request, exc: AuthRequiredException):
    encoded_next = quote(exc.next_page, safe="")
    return RedirectResponse(
        f"/login?next_page={encoded_next}",
        status_code=303,
    )