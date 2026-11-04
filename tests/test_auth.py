from starlette.testclient import TestClient


class TestRegistration:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "new@test.com",
                "password": "securepass123",
                "display_name": "New User",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_register_duplicate_username(self, client: TestClient, create_user):
        create_user("existing_user")
        response = client.post(
            "/register",
            data={
                "username": "existing_user",
                "email": "another@test.com",
                "password": "securepass123",
                "display_name": "Another",
            },
        )
        assert response.status_code == 400
        assert "уже" in response.text.lower() or "логин" in response.text.lower()

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@test.com",
                "password": "123",
                "display_name": "Test",
            },
        )
        assert response.status_code == 400


class TestLogin:
    def test_login_success(self, client: TestClient, create_user):
        create_user("alice", "password123")
        response = client.post(
            "/login",
            data={
                "username": "alice",
                "password": "password123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_login_wrong_password(self, client: TestClient, create_user):
        create_user("bob", "correct_password")
        response = client.post(
            "/login",
            data={
                "username": "bob",
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401

    def test_login_blocked_user(self, client: TestClient, create_user, db_session):
        user = create_user("blocked_user")
        user.is_banned = True
        db_session.commit()

        response = client.post(
            "/login",
            data={
                "username": "blocked_user",
                "password": "testpass123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 403
