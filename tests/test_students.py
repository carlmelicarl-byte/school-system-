from school_system.db import get_db


def test_student_directory_renders(client, auth):
    auth.login()
    response = client.get("/students/")
    assert response.status_code == 200
    assert b"Amani Kamau" in response.data
    assert b"EP/2026/001" in response.data


def test_admin_can_admit_a_student(app, client, auth):
    auth.login()
    token = auth.csrf("/students/new")
    response = client.post(
        "/students/new",
        data={
            "csrf_token": token,
            "admission_number": "EP/2026/099",
            "first_name": "Neema",
            "last_name": "Ali",
            "gender": "Female",
            "date_of_birth": "2013-04-01",
            "joined_on": "2026-08-29",
            "guardian_name": "Halima Ali",
            "guardian_phone": "0712 000 999",
            "class_id": "1",
            "status": "Active",
        },
    )
    assert response.status_code == 302
    assert "/students/" in response.headers["Location"]

    with app.app_context():
        student = get_db().execute(
            "SELECT * FROM students WHERE admission_number = 'EP/2026/099'"
        ).fetchone()
        assert student is not None
        assert student["first_name"] == "Neema"


def test_student_search_filters_results(client, auth):
    auth.login()
    response = client.get("/students/?q=Baraka&status=Active")
    assert b"Baraka Otieno" in response.data
    assert b"Amani Kamau" not in response.data
