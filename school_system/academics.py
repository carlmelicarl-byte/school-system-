import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_db, log_activity
from .security import login_required, roles_required


bp = Blueprint("academics", __name__, url_prefix="/classes")


@bp.get("/")
@login_required
def index():
    rows = get_db().execute(
        """SELECT c.*, COUNT(s.id) AS enrolled
           FROM classes c
           LEFT JOIN students s ON s.class_id = c.id AND s.status = 'Active'
           WHERE c.active = 1
           GROUP BY c.id
           ORDER BY c.grade, c.stream"""
    ).fetchall()
    return render_template("academics/classes.html", classes=rows)


def _class_from_form():
    name = request.form.get("name", "").strip()
    stream = request.form.get("stream", "").strip()
    teacher = request.form.get("class_teacher", "").strip()
    try:
        grade = int(request.form.get("grade", ""))
        capacity = int(request.form.get("capacity", ""))
    except ValueError:
        return None, "Grade and capacity must be whole numbers."

    if not name or not stream:
        return None, "Class name and stream are required."
    if not 1 <= grade <= 12:
        return None, "Grade must be between 1 and 12."
    if capacity < 1:
        return None, "Capacity must be at least 1."

    return (name, grade, stream, capacity, teacher or None), None


@bp.route("/new", methods=("GET", "POST"))
@roles_required("admin")
def create():
    if request.method == "POST":
        values, error = _class_from_form()
        if error:
            flash(error, "error")
        else:
            database = get_db()
            try:
                database.execute(
                    """INSERT INTO classes
                       (name, grade, stream, capacity, class_teacher)
                       VALUES (?, ?, ?, ?, ?)""",
                    values,
                )
                log_activity("Class created", values[0], g.user["id"])
                database.commit()
                flash(f"{values[0]} was created.", "success")
                return redirect(url_for("academics.index"))
            except sqlite3.IntegrityError:
                flash("A class with that name already exists.", "error")

    return render_template("academics/class_form.html", class_record=None)


@bp.route("/<int:class_id>/edit", methods=("GET", "POST"))
@roles_required("admin")
def edit(class_id):
    database = get_db()
    class_record = database.execute(
        "SELECT * FROM classes WHERE id = ? AND active = 1", (class_id,)
    ).fetchone()
    if class_record is None:
        return redirect(url_for("academics.index"))

    if request.method == "POST":
        values, error = _class_from_form()
        if error:
            flash(error, "error")
        else:
            try:
                database.execute(
                    """UPDATE classes SET name = ?, grade = ?, stream = ?,
                       capacity = ?, class_teacher = ? WHERE id = ?""",
                    (*values, class_id),
                )
                log_activity("Class updated", values[0])
                database.commit()
                flash("Class details updated.", "success")
                return redirect(url_for("academics.index"))
            except sqlite3.IntegrityError:
                flash("A class with that name already exists.", "error")

    return render_template("academics/class_form.html", class_record=class_record)
