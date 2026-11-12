from sqlalchemy import select
from starlette.testclient import TestClient

from app.models import Priority, Project, Status, Task


class TestTaskFiltering:
    def test_filter_by_status(self, client: TestClient, create_user, db_session, template_context):

        user = create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        for status in ["Новая", "В работе", "Выполнена"]:
            task = Task(
                title=f"Task {status}",
                description="мяу",
                project_id=project.id,
                status=status,
                author_id=user.id,
            )
            db_session.add(task)
        db_session.commit()

        response = client.get(f"/projects/{project.id}/tasks?status=Новая")
        assert response.status_code == 200

        tasks = template_context["tasks"]
        assert len(tasks) == 1
        assert tasks[0].status == Status.NEW
        assert template_context["total_count"] == 1

    def test_filter_by_priority(
        self, client: TestClient, create_user, db_session, template_context
    ):

        user = create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        for priority in ["Низкий", "Средний", "Высокий"]:
            task = Task(
                title=f"Task {priority}",
                description="мяу",
                author_id=user.id,
                project_id=project.id,
                priority=priority,
            )
            db_session.add(task)
        db_session.commit()

        response = client.get(f"/projects/{project.id}/tasks?priority=Высокий")
        assert response.status_code == 200

        tasks = template_context["tasks"]
        assert len(tasks) == 1
        assert tasks[0].priority == Priority.HIGH
        assert template_context["total_count"] == 1


class TestTaskSearch:
    def test_search_by_title(self, client: TestClient, create_user, db_session, template_context):

        user = create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        task1 = Task(title="Find mom for George", project_id=project.id, author_id=user.id)
        task2 = Task(title="Buy groceries", project_id=project.id, author_id=user.id)
        db_session.add_all([task1, task2])
        db_session.commit()

        client.post("/login", data={"username": "searcher", "password": "testpass123"})
        response = client.get(f"/projects/{project.id}/tasks?search=George")
        assert response.status_code == 200
        tasks = template_context["tasks"]
        assert len(tasks) == 1
        assert tasks[0].title == "Find mom for George"
        assert template_context["total_count"] == 1


class TestPagination:
    def test_pagination_default_page(
        self, client: TestClient, create_user, db_session, template_context
    ):

        user = create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        for i in range(15):
            task = Task(title=f"Task {i}", project_id=project.id, author_id=user.id)
            db_session.add(task)
        db_session.commit()

        client.post("/login", data={"username": "pager", "password": "testpass123"})
        response = client.get(f"/projects/{project.id}/tasks")
        assert response.status_code == 200
        tasks = template_context["tasks"]
        assert len(tasks) == 15

    def test_pagination_preserves_filters(
        self, client: TestClient, create_user, db_session, template_context
    ):

        user = create_user("member")

        client.post("/login", data={"username": "member", "password": "testpass123"})

        client.post(
            "/projects/create", data={"name": "test project", "description": "Test Description"}
        )

        project = db_session.scalar(select(Project).where(Project.name == "test project"))

        for i in range(15):
            task = Task(title=f"Task {i}", project_id=project.id, status="Новая", author_id=user.id)
            db_session.add(task)
        db_session.commit()

        response = client.get(f"/projects/{project.id}/tasks?status=Новая&page=2")
        assert response.status_code == 200
        status = template_context["status"]
        assert status == "Новая"
