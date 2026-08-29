def test_login_is_required(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_admin_can_log_in_and_out(client, auth):
    response = auth.login()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    response = client.get("/")
    assert response.status_code == 200
    assert b"Good day, Amina" in response.data

    token = auth.csrf()
    response = client.post("/auth/logout", data={"csrf_token": token})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_invalid_password_is_rejected(client, auth):
    response = auth.login(password="not-the-password")
    assert response.status_code == 200
    assert b"email or password is incorrect" in response.data


def test_csrf_is_required(client):
    response = client.post(
        "/auth/login",
        data={"email": "admin@school.local", "password": "ChangeMe123!"},
    )
    assert response.status_code == 400


def test_teacher_cannot_open_admin_forms(client, auth):
    auth.login("teacher@school.local", "Teacher123!")
    assert client.get("/students/new").status_code == 403
    assert client.get("/finance/").status_code == 403
