from datetime import date, timedelta

from flask import Blueprint, render_template

from .db import get_db, setting
from .security import login_required


bp = Blueprint("dashboard", __name__)


@bp.get("/")
@login_required
def index():
    database = get_db()
    counts = database.execute(
        """SELECT
             (SELECT COUNT(*) FROM students WHERE status = 'Active') AS students,
             (SELECT COUNT(*) FROM classes WHERE active = 1) AS classes,
             (SELECT COUNT(*) FROM users WHERE role = 'teacher' AND active = 1) AS teachers,
             (SELECT COUNT(*) FROM students WHERE class_id IS NULL AND status = 'Active') AS unassigned"""
    ).fetchone()

    finance = database.execute(
        """SELECT
             COALESCE((SELECT SUM(amount) FROM fee_invoices), 0) AS billed,
             COALESCE((SELECT SUM(amount) FROM payments), 0) AS paid"""
    ).fetchone()

    today = date.today().isoformat()
    attendance = database.execute(
        """SELECT
             COUNT(*) AS marked,
             SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS present
           FROM attendance WHERE attendance_date = ?""",
        (today,),
    ).fetchone()

    if attendance["marked"] == 0:
        latest = database.execute(
            "SELECT MAX(attendance_date) AS day FROM attendance"
        ).fetchone()["day"]
        if latest:
            attendance = database.execute(
                """SELECT COUNT(*) AS marked,
                     SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS present
                   FROM attendance WHERE attendance_date = ?""",
                (latest,),
            ).fetchone()
            attendance_day = latest
        else:
            attendance_day = today
    else:
        attendance_day = today

    class_rows = database.execute(
        """SELECT c.id, c.name, c.capacity, COUNT(s.id) AS enrolled
           FROM classes c
           LEFT JOIN students s ON s.class_id = c.id AND s.status = 'Active'
           WHERE c.active = 1
           GROUP BY c.id
           ORDER BY c.grade, c.stream"""
    ).fetchall()

    recent_payments = database.execute(
        """SELECT p.*, s.first_name || ' ' || s.last_name AS student_name
           FROM payments p JOIN students s ON s.id = p.student_id
           ORDER BY p.paid_on DESC, p.id DESC LIMIT 5"""
    ).fetchall()

    activities = database.execute(
        """SELECT a.*, u.full_name
           FROM activity_log a LEFT JOIN users u ON u.id = a.user_id
           ORDER BY a.id DESC LIMIT 5"""
    ).fetchall()

    return render_template(
        "dashboard/index.html",
        counts=counts,
        finance=finance,
        attendance=attendance,
        attendance_day=attendance_day,
        class_rows=class_rows,
        recent_payments=recent_payments,
        activities=activities,
        term=setting("current_term", "1"),
        year=setting("academic_year", str(date.today().year)),
    )
