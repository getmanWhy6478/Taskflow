from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import Priority, Project, Status, Task, User


class TestCommentCreation:
    def test_create_comment_success(self, client: TestClient, create_user, db_session):

        user = create_user("commenter")

        client.post(
            "/register",
            data={
                "username": "qwertyuiop[]",
                "password": "qwertyuiop[]",
                "display_name": "qwertyuiop[]",
                "email": "qwertahdhdak@",
            },
        )

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

        response = client.post(
            "/projects/create",
            data={"name": "test project", "description": "Test Description"},
            follow_redirects=True,
        )
        print("=" * 50)
        print("STATUS:", response.status_code)
        print("HEADERS:", dict(response.headers))
        print("BODY:", response.text)
        print("=" * 50)

        assert response.status_code in (200, 303), f"Проект не создался: {response.text}"

        project = db_session.scalar(select(Project).where(Project.name == "test project"))
        user = db_session.scalar(select(User).where(User.username == "qwertyuiop[]"))

        print("User: ", user.username)
        print("Project: ", project.id)

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

        response = client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        assert response.status_code == 303


class TestCommentRead:
    def test_view_comments(self, client: TestClient, create_user, db_session):

        user = create_user("commenter")

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

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
        client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200


class TestCommentDelete:
    def test_delete_comment(self, client: TestClient, create_user, db_session):
        from app.models import Comment

        user = create_user("commenter")

        client.post("/login", data={"username": "commenter", "password": "testpass123"})

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

        client.post(
            f"/tasks/{task.id}/comments", data={"text": "Great task!"}, follow_redirects=False
        )
        comment = db_session.scalar(select(Comment).where(Comment.body == "Great task!"))
        response = client.post(f"/comments/{comment.id}/delete", follow_redirects=False)
        assert response.status_code == 303

        deleted = db_session.scalar(select(Comment).where(Comment.body == "Great task!"))
        assert deleted is None

    def test_cannot_delete_others_comment(self, client: TestClient, create_user, db_session):
        from app.models import Comment

        owner = create_user("owner")
        client.post("/login", data={"username": "owner", "password": "testpass123"})
        create_user("outsider")
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
