from starlette.testclient import TestClient

from app.models import Project, Status, Priority, Task
from sqlalchemy import select

from tests.conftest import db_session


class TestCommentCreation:
    def test_create_comment_success(
        self, client: TestClient, create_user, create_project, db_session
    ):
        from app.models import Task

        user = create_user("commenter")

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "Test Project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "Test Project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "Test Task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        response = client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        assert response.status_code == 303


class TestCommentRead:
    def test_view_comments(self, client: TestClient, create_user, create_project, db_session):
        from app.models import Task, Comment

        user = create_user("commenter")

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "Test Project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "Test Project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "Test Task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))
        client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200


class TestCommentDelete:
    def test_delete_comment(self, client: TestClient, create_user, create_project, db_session):
        from app.models import Task, Comment

        user = create_user("commenter")

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "Test Project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "Test Project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "Test Task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": user.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        comment = db_session.scalar(select(Comment).where(Comment.body == "Great task!"))
        response = client.post(f"/comments/{comment.id}/delete", follow_redirects=False)
        assert response.status_code == 303

        deleted = db_session.scalar(select(Comment).where(Comment.body == "Great task!"))
        assert deleted is None

    def test_cannot_delete_others_comment(
        self, client: TestClient, create_user, create_project, db_session
    ):
        from app.models import Task, Comment

        owner = create_user("owner")
        client.post("/login", data={"username": "owner", "password": "testpass123"})
        outsider = create_user("outsider")
        client.post(
            "/projects/create", data={"name": "Test Project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "Test Project"))

        client.post(
            f"/projects/{project.id}/tasks/create",
            data={
                "title": "Test Task",
                "description": "Test Description",
                "priority": Priority.MEDIUM.value,
                "status": Status.NEW.value,
                "author_id": owner.id,
            },
            follow_redirects=False,
        )
        task = db_session.scalar(select(Task).where(Task.title == "test task"))

        client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        comment = db_session.scalar(select(Comment).where(Comment.body == "Great task!"))

        client.post("/login", data={"username": "outsider", "password": "testpass123"})
        response = client.post(f"/comments/{comment.id}/delete", follow_redirects=False)

        assert response.status_code == 403
