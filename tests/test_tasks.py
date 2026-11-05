from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import Priority, Project, Status, Task

from tests.conftest import db_session


class TestTaskCreation:
    def test_create_task_success(self, client: TestClient, create_user, db_session):
        user = create_user("creator")
        client.post("/login", data={"username": "creator", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))
        response = client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "New Task",
                "description": "Task description",
                "author_id": user.id,
                "priority": Priority.MEDIUM,
                "status": Status.IN_WORK,
            },
            follow_redirects=False,
        )
        db_session.scalar(select(Task).where(Task.title == "New Task"))
        assert response.status_code == 303


class TestTaskRead:
    def test_view_task(self, client: TestClient, create_user, db_session):
        from app.models import Priority, Project, Status, Task

        user = create_user("viewer")

        client.post("/login", data={"username": "viewer", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "test task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.IN_WORK.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )

        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        assert task is not None

        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200


class TestTaskUpdate:
    def test_update_task_status(self, client: TestClient, create_user, db_session):
        from app.models import Task

        user = create_user("viewer")

        client.post("/login", data={"username": "viewer", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "test task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.IN_WORK.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))
        response = client.post(
            f"/tasks/{task.id}/status", data={"status": Status.DONE.value}, follow_redirects=False
        )
        assert response.status_code == 303

        assert task.status.value == Status.DONE.value

    def test_invalid_status_transition(
        self, client: TestClient, create_user, db_session
    ):
        from app.models import Task

        user = create_user("updater")

        client.post("/login", data={"username": "updater", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "test task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        response = client.post(f"/tasks/{task.id}/status", data={"status": Status.DONE.value})
        assert response.status_code == 400


class TestTaskDelete:
    def test_delete_task(self, client: TestClient, create_user, db_session):
        from app.models import Task

        user = create_user("deleter")

        client.post("/login", data={"username": "deleter", "password": "testpass123"})
        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "test task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        response = client.post(f"/tasks/{task.id}/delete", follow_redirects=False)
        assert response.status_code == 303

        deleted_task = db_session.scalar(select(Task).where(Task.id == task.id))
        assert deleted_task is None
