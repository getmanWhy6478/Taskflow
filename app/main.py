from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router

app = FastAPI(title="TaskFlow")

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(task_router)

Base.metadata.create_all(bind=engine)


@app.get("/")
def index():
    return RedirectResponse("/register", status_code=303)
