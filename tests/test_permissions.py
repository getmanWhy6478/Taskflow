from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import Project

from tests.conftest import db_session


class TestGuestAccess:
    def test_guest_cannot_access_projects(self, client: TestClient):
        response = client.get("/projects", follow_redirects=False)
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    def test_guest_cannot_access_task(self, client: TestClient):
        response = client.get("/tasks/1", follow_redirects=False)
        assert response.status_code == 303


class TestProjectPermissions:
    def test_member_can_view_project(
        self, client: TestClient, create_user, db_session
    ):
        create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        response = client.get(f"/projects/{project.id}", follow_redirects=False)
        assert response.status_code == 200

    def test_non_member_cannot_view_private_project(
        self, client: TestClient, create_user, create_project
    ):
        owner = create_user("owner")
        create_user("outsider")
        project = create_project("Private Project", owner.id)

        client.post(
            "/login",
            data={"username": "outsider", "password": "testpass123"},
            follow_redirects=False,
        )

        response = client.get(f"/projects/{project.id}")
        assert response.status_code == 403

    def test_only_owner_can_delete_project(self, client: TestClient, create_user, create_project):
        owner = create_user("owner")
        create_user("member")
        project = create_project("test project", owner.id)

        client.post("/login", data={"username": "member", "password": "testpass123"})

        response = client.post(f"/projects/{project.id}/delete")
        assert response.status_code in [403, 404]


class TestAdminPermissions:
    def test_admin_can_access_admin_panel(self, client: TestClient, create_user):
        create_user("admin", is_admin=True)
        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.get("/admin/users")
        assert response.status_code == 200

    def test_regular_user_cannot_access_admin_panel(self, client: TestClient, create_user):
        create_user("regular_user")
        client.post("/login", data={"username": "regular_user", "password": "testpass123"})

        response = client.get("/admin/users")
        assert response.status_code == 403
