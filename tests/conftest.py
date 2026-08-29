import pytest

from school_system import create_app
from school_system.db import get_db, init_db, seed_demo


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "AUTO_INIT_DB": False,
        }
    )
    with application.app_context():
        init_db()
        seed_demo()
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self.client = client

    def login(self, email="admin@school.local", password="ChangeMe123!"):
        self.client.get("/auth/login")
        with self.client.session_transaction() as session:
            token = session["_csrf_token"]
        return self.client.post(
            "/auth/login",
            data={"email": email, "password": password, "csrf_token": token},
        )

    def csrf(self, path="/"):
        self.client.get(path)
        with self.client.session_transaction() as session:
            return session["_csrf_token"]


@pytest.fixture()
def auth(client):
    return AuthActions(client)
