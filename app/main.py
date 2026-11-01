from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from app.routes.admin import router as admin_router
from app.routes.comments import router as comment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.profile import router as profile_router

app = FastAPI(title="TaskFlow")

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

Base.metadata.create_all(bind=engine)


@app.get("/")
def index():
    return RedirectResponse("/dashboard", status_code=303)


