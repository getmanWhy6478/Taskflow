from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.dependencies import AuthRequiredException
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


class CsrfSettings(BaseModel):
    secret_key: str = settings.secret_key
    cookie_samesite: str = "lax"
    cookie_secure: bool = True
    cookie_key: str = "csrf_token"
    header_name: str = "X-CSRF-Token"


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        protected_methods = "POST"

        excluded_paths = {
            "/login",
            "/register",
        }

        csrf_protect = CsrfProtect()

        if request.method == "GET":
            response = await call_next(request)
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            csrf_protect.set_csrf_cookie(signed_token, response)
            return response

        # Для мутирующих запросов проверяем токен
        if request.method in protected_methods and request.url.path not in excluded_paths:
            try:
                csrf_protect.validate_csrf(request)
            except CsrfProtectError:
                return JSONResponse(
                    status_code=403, content={"detail": "CSRF token validation failed"}
                )

        response = await call_next(request)
        return response


app.add_middleware(CSRFMiddleware)


@app.exception_handler(CsrfProtectError)
def csrf_validation_error(request: Request, exc: CsrfProtectError):
    return HTTPException(status_code=400, detail={"detail": "CSRF token mismatch"})


@app.get("/get-csrf-token")
def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = JSONResponse(content={"csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


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
def http_exception_handler(request: Request, exc: HTTPException):
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
def auth_required_handler(request: Request, exc: AuthRequiredException):
    encoded_next = quote(exc.next_page, safe="")
    return RedirectResponse(
        f"/login?next_page={encoded_next}",
        status_code=303,
    )
