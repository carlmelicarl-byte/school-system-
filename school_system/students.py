import sqlite3
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import get_db, log_activity
from .security import login_required, roles_required


bp = Blueprint("students", __name__, url_prefix="/students")


def get_student(student_id):
    student = get_db().execute(
        """SELECT s.*, c.name AS class_name
           FROM students s LEFT JOIN classes c ON c.id = s.class_id
           WHERE s.id = ?""",
        (student_id,),
    ).fetchone()
    if student is None:
        abort(404)
    return student


def active_classes():
    return get_db().execute(
        "SELECT id, name FROM classes WHERE active = 1 ORDER BY grade, stream"
    ).fetchall()


@bp.get("/")
@login_required
def index():
    query = request.args.get("q", "").strip()
    class_id = request.args.get("class_id", type=int)
    status = request.args.get("status", "Active")

    sql = """SELECT s.*, c.name AS class_name
             FROM students s LEFT JOIN classes c ON c.id = s.class_id
             WHERE 1 = 1"""
    params = []
    if query:
        sql += """ AND (s.first_name || ' ' || s.last_name LIKE ?
                    OR s.admission_number LIKE ? OR s.guardian_name LIKE ?)"""
        search = f"%{query}%"
        params.extend([search, search, search])
    if class_id:
        sql += " AND s.class_id = ?"
        params.append(class_id)
    if status:
        sql += " AND s.status = ?"
        params.append(status)
    sql += " ORDER BY s.first_name, s.last_name"

    students = get_db().execute(sql, params).fetchall()
    return render_template(
        "students/index.html",
        students=students,
        classes=active_classes(),
        query=query,
        selected_class=class_id,
        selected_status=status,
    )


def _student_from_form():
    values = {
        "admission_number": request.form.get("admission_number", "").strip().upper(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "gender": request.form.get("gender", ""),
        "date_of_birth": request.form.get("date_of_birth", "") or None,
        "joined_on": request.form.get("joined_on", "") or date.today().isoformat(),
        "guardian_name": request.form.get("guardian_name", "").strip(),
        "guardian_phone": request.form.get("guardian_phone", "").strip(),
        "class_id": request.form.get("class_id", type=int),
        "status": request.form.get("status", "Active"),
    }
    required = ("admission_number", "first_name", "last_name", "guardian_name", "guardian_phone")
    if any(not values[key] for key in required):
        return values, "Complete all required fields."
    if values["gender"] not in ("Female", "Male", "Other"):
        return values, "Select a valid gender."
    if values["status"] not in ("Active", "Graduated", "Transferred", "Inactive"):
        return values, "Select a valid status."
    return values, None


@bp.route("/new", methods=("GET", "POST"))
@roles_required("admin")
def create():
    values = None
    if request.method == "POST":
        values, error = _student_from_form()
        if error:
            flash(error, "error")
        else:
            database = get_db()
            try:
                cursor = database.execute(
                    """INSERT INTO students
                       (admission_number, first_name, last_name, gender, date_of_birth,
                        joined_on, guardian_name, guardian_phone, class_id, status)
                       VALUES (:admission_number, :first_name, :last_name, :gender,
                        :date_of_birth, :joined_on, :guardian_name, :guardian_phone,
                        :class_id, :status)""",
                    values,
                )
                log_activity(
                    "Student admitted",
                    f"{values['first_name']} {values['last_name']} · {values['admission_number']}",
                    g.user["id"],
                )
                database.commit()
                flash("Student admitted successfully.", "success")
                return redirect(url_for("students.detail", student_id=cursor.lastrowid))
            except sqlite3.IntegrityError:
                flash("That admission number is already in use.", "error")

    return render_template(
        "students/form.html", student=values, classes=active_classes(), title="Admit student"
    )


@bp.get("/<int:student_id>")
@login_required
def detail(student_id):
    student = get_student(student_id)
    database = get_db()
    invoices = database.execute(
        "SELECT * FROM fee_invoices WHERE student_id = ? ORDER BY academic_year DESC, term DESC",
        (student_id,),
    ).fetchall()
    payments = database.execute(
        "SELECT * FROM payments WHERE student_id = ? ORDER BY paid_on DESC, id DESC",
        (student_id,),
    ).fetchall()
    totals = database.execute(
        """SELECT
             COALESCE((SELECT SUM(amount) FROM fee_invoices WHERE student_id = ?), 0) AS billed,
             COALESCE((SELECT SUM(amount) FROM payments WHERE student_id = ?), 0) AS paid""",
        (student_id, student_id),
    ).fetchone()
    return render_template(
        "students/detail.html",
        student=student,
        invoices=invoices,
        payments=payments,
        totals=totals,
    )


@bp.route("/<int:student_id>/edit", methods=("GET", "POST"))
@roles_required("admin")
def edit(student_id):
    student = get_student(student_id)
    values = dict(student)
    if request.method == "POST":
        values, error = _student_from_form()
        if error:
            flash(error, "error")
        else:
            database = get_db()
            values["id"] = student_id
            try:
                database.execute(
                    """UPDATE students SET
                       admission_number = :admission_number, first_name = :first_name,
                       last_name = :last_name, gender = :gender,
                       date_of_birth = :date_of_birth, joined_on = :joined_on,
                       guardian_name = :guardian_name, guardian_phone = :guardian_phone,
                       class_id = :class_id, status = :status
                       WHERE id = :id""",
                    values,
                )
                log_activity("Student updated", values["admission_number"], g.user["id"])
                database.commit()
                flash("Student record updated.", "success")
                return redirect(url_for("students.detail", student_id=student_id))
            except sqlite3.IntegrityError:
                flash("That admission number is already in use.", "error")

    return render_template(
        "students/form.html", student=values, classes=active_classes(), title="Edit student"
    )
