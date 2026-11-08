from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import User


class TestAdminUsersView:
    def test_admin_can_view_users(self, client: TestClient, create_user, db_session):
        create_user("admin", is_admin=True)
        create_user("regular_user")

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.get("/admin/users")
        assert response.status_code == 200
        assert "regular_user" in response.text

    def test_guest_cannot_view_users(self, client: TestClient):
        response = client.get("/admin/users", follow_redirects=False)
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    def test_regular_user_cannot_view_users(self, client: TestClient, create_user, db_session):
        create_user("regular", is_admin=False)

        client.post("/login", data={"username": "regular", "password": "testpass123"})

        response = client.get("/admin/users")
        assert response.status_code == 403


class TestBanUser:
    def test_admin_can_ban_user(self, client: TestClient, create_user, db_session):
        create_user("admin", is_admin=True)
        target = create_user("target")

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-active",
            follow_redirects=False,
        )
        assert response.status_code == 303

        banned_user = db_session.scalar(select(User).where(User.username == "target"))
        assert banned_user is not None
        assert banned_user.is_banned is True

    def test_admin_cannot_ban_himself(self, client: TestClient, create_user, db_session):
        admin = create_user("admin", is_admin=True)

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{admin.id}/toggle-active",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_guest_cannot_ban_user(self, client: TestClient, create_user, db_session):
        target = create_user("target")

        response = client.post(
            f"/admin/users/{target.id}/toggle-active",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    def test_regular_user_cannot_ban(self, client: TestClient, create_user, db_session):
        create_user("regular", is_admin=False)
        target = create_user("target")

        client.post("/login", data={"username": "regular", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-active",
        )
        assert response.status_code == 403


class TestUnbanUser:
    def test_admin_can_unban_user(self, client: TestClient, create_user, db_session):
        create_user("admin", is_admin=True)
        target = create_user("target", is_banned=True)

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-active/unblock",
            follow_redirects=False,
        )
        assert response.status_code == 303

        unbanned_user = db_session.scalar(select(User).where(User.username == "target"))
        assert unbanned_user is not None
        assert unbanned_user.is_banned is False

    def test_guest_cannot_unban_user(self, client: TestClient, create_user, db_session):
        target = create_user("target", is_banned=True)

        response = client.post(
            f"/admin/users/{target.id}/toggle-active/unblock",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")


class TestMakeAdmin:
    def test_admin_can_make_user_admin(self, client: TestClient, create_user, db_session):
        create_user("admin", is_admin=True)
        target = create_user("target", is_admin=False)

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-admin",
            data={"action": "make_admin"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        new_admin = db_session.scalar(select(User).where(User.username == "target"))
        assert new_admin is not None
        assert new_admin.is_admin is True

    def test_admin_can_remove_admin_rights(self, client: TestClient, create_user, db_session):
        create_user("admin", is_admin=True)
        target = create_user("target", is_admin=True)

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-admin",
            data={"action": "remove_admin"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        ex_admin = db_session.scalar(select(User).where(User.username == "target"))
        assert ex_admin is not None
        assert ex_admin.is_admin is False

    def test_admin_cannot_change_himself(self, client: TestClient, create_user, db_session):
        admin = create_user("admin", is_admin=True)

        client.post("/login", data={"username": "admin", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{admin.id}/toggle-admin",
            data={"action": "remove_admin"},
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_guest_cannot_change_admin_rights(self, client: TestClient, create_user, db_session):
        target = create_user("target", is_admin=False)

        response = client.post(
            f"/admin/users/{target.id}/toggle-admin",
            data={"action": "make_admin"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    def test_regular_user_cannot_change_admin_rights(
        self, client: TestClient, create_user, db_session
    ):
        create_user("regular", is_admin=False)
        target = create_user("target", is_admin=False)

        client.post("/login", data={"username": "regular", "password": "testpass123"})

        response = client.post(
            f"/admin/users/{target.id}/toggle-admin",
            data={"action": "make_admin"},
        )
        assert response.status_code == 403
