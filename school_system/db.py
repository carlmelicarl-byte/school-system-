import sqlite3
from datetime import date, timedelta
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


def get_db():
    """Return one SQLite connection per application context."""
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    connection = get_db()
    with current_app.open_resource("schema.sql") as schema:
        connection.executescript(schema.read().decode("utf-8"))
    connection.commit()


def setting(key, default=None):
    row = get_db().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def log_activity(action, details=None, user_id=None):
    connection = get_db()
    connection.execute(
        "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details),
    )


def seed_demo():
    """Populate a deterministic, compact dataset for local development."""
    connection = get_db()

    settings = {
        "school_name": "ElimuPro Academy",
        "school_motto": "Learn. Lead. Serve.",
        "academic_year": "2026",
        "current_term": "2",
        "currency": "KES",
    }
    connection.executemany(
        "INSERT INTO settings (key, value) VALUES (?, ?)", settings.items()
    )

    users = [
        ("Amina Njeri", "admin@school.local", "admin", "ChangeMe123!"),
        ("Daniel Otieno", "teacher@school.local", "teacher", "Teacher123!"),
        ("Grace Wanjiku", "bursar@school.local", "bursar", "Bursar123!"),
    ]
    connection.executemany(
        "INSERT INTO users (full_name, email, role, password_hash) VALUES (?, ?, ?, ?)",
        [(name, email, role, generate_password_hash(password)) for name, email, role, password in users],
    )

    classes = [
        ("Grade 7 North", 7, "North", 40, "Daniel Otieno"),
        ("Grade 7 South", 7, "South", 40, "Mercy Achieng"),
        ("Grade 8 North", 8, "North", 42, "Peter Mwangi"),
        ("Grade 9 East", 9, "East", 38, "Faith Chebet"),
    ]
    connection.executemany(
        """INSERT INTO classes (name, grade, stream, capacity, class_teacher)
           VALUES (?, ?, ?, ?, ?)""",
        classes,
    )
    class_ids = {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM classes").fetchall()
    }

    students = [
        ("EP/2026/001", "Amani", "Kamau", "Female", "2013-03-14", "Mary Kamau", "0712 440 118", "Grade 7 North"),
        ("EP/2026/002", "Baraka", "Otieno", "Male", "2012-11-02", "Janet Otieno", "0722 156 840", "Grade 7 North"),
        ("EP/2026/003", "Chebet", "Kiptoo", "Female", "2013-07-26", "Paul Kiptoo", "0701 620 994", "Grade 7 North"),
        ("EP/2026/004", "David", "Mutua", "Male", "2012-09-18", "Lucy Mutua", "0733 201 745", "Grade 7 South"),
        ("EP/2026/005", "Imani", "Wekesa", "Female", "2013-01-09", "Mark Wekesa", "0740 335 266", "Grade 7 South"),
        ("EP/2026/006", "Jabali", "Mwangi", "Male", "2012-05-30", "Rose Mwangi", "0791 407 532", "Grade 7 South"),
        ("EP/2026/007", "Malaika", "Omondi", "Female", "2011-04-21", "James Omondi", "0757 884 103", "Grade 8 North"),
        ("EP/2026/008", "Nuru", "Njoroge", "Male", "2011-12-11", "Agnes Njoroge", "0721 993 410", "Grade 8 North"),
        ("EP/2026/009", "Sifa", "Musyoka", "Female", "2011-08-07", "John Musyoka", "0115 220 875", "Grade 8 North"),
        ("EP/2026/010", "Taji", "Ochieng", "Male", "2010-02-17", "Naomi Ochieng", "0715 309 664", "Grade 9 East"),
        ("EP/2026/011", "Zuri", "Wafula", "Female", "2010-06-25", "Kevin Wafula", "0735 742 901", "Grade 9 East"),
        ("EP/2026/012", "Kito", "Maina", "Male", "2010-10-13", "Esther Maina", "0745 138 552", "Grade 9 East"),
    ]
    joined_on = "2026-01-06"
    connection.executemany(
        """INSERT INTO students
           (admission_number, first_name, last_name, gender, date_of_birth,
            joined_on, guardian_name, guardian_phone, class_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (adm, first, last, gender, dob, joined_on, guardian, phone, class_ids[class_name])
            for adm, first, last, gender, dob, guardian, phone, class_name in students
        ],
    )

    student_rows = connection.execute(
        "SELECT id, admission_number FROM students ORDER BY id"
    ).fetchall()
    due_date = "2026-06-30"
    for index, student in enumerate(student_rows):
        tuition = 18000 if index < 6 else 21000
        connection.execute(
            """INSERT INTO fee_invoices
               (student_id, academic_year, term, description, amount, due_date)
               VALUES (?, 2026, 2, 'Term 2 tuition and activities', ?, ?)""",
            (student["id"], tuition, due_date),
        )

        paid = [18000, 12000, 9000, 18000, 14000, 6000, 21000, 15000, 10500, 21000, 16000, 8000][index]
        cursor = connection.execute(
            """INSERT INTO payments
               (student_id, amount, method, reference, paid_on, notes, recorded_by)
               VALUES (?, ?, ?, ?, ?, 'Term 2 payment', 3)""",
            (
                student["id"],
                paid,
                "M-PESA" if index % 3 else "Bank",
                f"QK{index + 31:06d}",
                f"2026-08-{(index % 18) + 1:02d}",
            ),
        )
        receipt = f"RCT-2026-{cursor.lastrowid:05d}"
        connection.execute(
            "UPDATE payments SET receipt_number = ? WHERE id = ?",
            (receipt, cursor.lastrowid),
        )

    attendance_days = [date(2026, 8, 24) + timedelta(days=offset) for offset in range(5)]
    for day_index, attendance_day in enumerate(attendance_days):
        if attendance_day.weekday() >= 5:
            continue
        for index, student in enumerate(student_rows):
            class_id = connection.execute(
                "SELECT class_id FROM students WHERE id = ?", (student["id"],)
            ).fetchone()["class_id"]
            status = "Present"
            if (index + day_index) % 13 == 0:
                status = "Absent"
            elif (index + day_index) % 9 == 0:
                status = "Late"
            connection.execute(
                """INSERT INTO attendance
                   (student_id, class_id, attendance_date, status)
                   VALUES (?, ?, ?, ?)""",
                (student["id"], class_id, attendance_day.isoformat(), status),
            )

    admin_id = connection.execute(
        "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()["id"]
    activities = [
        (admin_id, "New academic year configured", "Term 2, 2026"),
        (admin_id, "Student records imported", "12 learner profiles added"),
        (admin_id, "Fee structure published", "Term 2 invoices generated"),
    ]
    connection.executemany(
        "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
        activities,
    )
    connection.commit()


@click.command("init-db")
@click.option("--with-demo", is_flag=True, help="Load the local demonstration dataset.")
@with_appcontext
def init_db_command(with_demo):
    """Create a fresh database, optionally including demo data."""
    init_db()
    if with_demo:
        seed_demo()
    click.echo("Database initialized" + (" with demo data." if with_demo else "."))


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
