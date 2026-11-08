from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import User


class TestProfileView:
    def test_view_profile(self, client: TestClient, create_user, db_session):
        create_user("viewer")
        client.post("/login", data={"username": "viewer", "password": "testpass123"})

        response = client.get("/profile")
        assert response.status_code == 200

    def test_guest_cannot_view_profile(self, client: TestClient):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 303


class TestProfileNameChange:
    def test_change_name_success(self, client: TestClient, create_user, db_session):
        create_user("old_name")
        client.post("/login", data={"username": "old_name", "password": "testpass123"})

        response = client.post(
            "/profile",
            data={"action": "change_name", "new_name": "new_name"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        updated_user = db_session.scalar(select(User).where(User.display_name == "new_name"))
        assert updated_user is not None
        assert updated_user.display_name == "new_name"

    def test_guest_cannot_change_name(self, client: TestClient):
        response = client.post(
            "/profile",
            data={
                "action": "change_name",
                "new_name": "hacker",
                "new_password": "",
                "current_password": "",
                "confirm_password": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")


class TestProfilePasswordChange:
    def test_change_password_success(self, client: TestClient, create_user, db_session):
        create_user("password_changer")
        client.post("/login", data={"username": "password_changer", "password": "testpass123"})

        response = client.post(
            "/profile",
            data={
                "action": "change_password",
                "current_password": "testpass123",
                "new_password": "new_secure_password",
                "confirm_password": "new_secure_password",
                "new_name": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_change_password_empty_fields(self, client: TestClient, create_user, db_session):
        create_user("empty_fields")
        client.post("/login", data={"username": "empty_fields", "password": "testpass123"})

        response = client.post(
            "/profile",
            data={
                "action": "change_password",
                "current_password": "",
                "new_password": "",
                "confirm_password": "",
                "new_name": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Все поля пароля обязательны" in response.text

    def test_change_password_mismatch(self, client: TestClient, create_user, db_session):
        create_user("mismatch")
        client.post("/login", data={"username": "mismatch", "password": "testpass123"})

        response = client.post(
            "/profile",
            data={
                "action": "change_password",
                "current_password": "testpass123",
                "new_password": "new_pass_1",
                "confirm_password": "new_pass_2",
                "new_name": "",
            },
        )
        assert response.status_code == 200
        assert "Пароли не совпадают" in response.text

    def test_change_password_wrong_current(self, client: TestClient, create_user, db_session):
        create_user("wrong_current")
        client.post("/login", data={"username": "wrong_current", "password": "testpass123"})

        response = client.post(
            "/profile",
            data={
                "action": "change_password",
                "current_password": "wrong_password",
                "new_password": "new_secure_password",
                "confirm_password": "new_secure_password",
                "new_name": "",
            },
        )
        assert response.status_code == 200
        assert "Неверный текущий пароль" in response.text

    def test_guest_cannot_change_password(self, client: TestClient):
        response = client.post(
            "/profile",
            data={
                "action": "change_password",
                "current_password": "old",
                "new_password": "new",
                "confirm_password": "new",
                "new_name": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")
