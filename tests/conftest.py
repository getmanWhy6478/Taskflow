import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.project_members import ProjectsMember
from app.models.projects import Project
from app.models.users import User
from app.services.auth_services import hash_password
from app.templates.templates import templates

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.engine = engine
Base.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def create_user(db_session: Session):
    def _create_user(username: str, password: str = "testpass123", is_admin: bool = False):
        user = User(
            username=username,
            email=f"{username}@test.com",
            display_name=username,
            password_hash=hash_password(password),
            is_admin=is_admin,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def create_project(db_session: Session):
    def _create_project(name: str, owner_id: int):
        project = Project(name=name, owner_id=owner_id, description="Test project")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        return project

    return _create_project


@pytest.fixture
def create_project_member(db_session: Session):
    def _create_project_member(author_id: int, owner_id: int, role: str = "member"):
        projectmember = ProjectsMember(author_id=author_id, owner_id=owner_id, role=role)
        db_session.add(projectmember)
        db_session.commit()
        db_session.refresh(projectmember)
        return projectmember

    return _create_project_member


@pytest.fixture
def template_context(monkeypatch):
    captured = {}
    original = templates.TemplateResponse

    def wrapper(*args, **kwargs):
        response = original(*args, **kwargs)
        captured.clear()
        captured.update(response.context)
        return response

    monkeypatch.setattr(templates, "TemplateResponse", wrapper)
    return captured
