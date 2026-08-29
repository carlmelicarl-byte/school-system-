from school_system.db import get_db


def test_bursar_can_record_payment(app, client, auth):
    auth.login("bursar@school.local", "Bursar123!")
    token = auth.csrf("/finance/payments/new?student_id=1")
    response = client.post(
        "/finance/payments/new",
        data={
            "csrf_token": token,
            "student_id": "1",
            "amount": "2500",
            "paid_on": "2026-08-29",
            "method": "M-PESA",
            "reference": "TESTREF001",
            "notes": "Test payment",
        },
    )
    assert response.status_code == 302
    assert "/receipt" in response.headers["Location"]

    with app.app_context():
        payment = get_db().execute(
            "SELECT * FROM payments WHERE reference = 'TESTREF001'"
        ).fetchone()
        assert payment["amount"] == 2500
        assert payment["receipt_number"].startswith("RCT-2026-")


def test_receipt_renders(client, auth):
    auth.login("bursar@school.local", "Bursar123!")
    response = client.get("/finance/payments/1/receipt")
    assert response.status_code == 200
    assert b"PAYMENT RECEIPT" in response.data
    assert b"RCT-2026-00001" in response.data
