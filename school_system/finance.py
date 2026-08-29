from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db, log_activity, setting
from .security import roles_required
from .students import get_student


bp = Blueprint("finance", __name__, url_prefix="/finance")


@bp.get("/")
@roles_required("admin", "bursar")
def index():
    query = request.args.get("q", "").strip()
    sql = """SELECT s.id, s.admission_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    c.name AS class_name,
                    COALESCE((SELECT SUM(i.amount) FROM fee_invoices i WHERE i.student_id = s.id), 0) AS billed,
                    COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.student_id = s.id), 0) AS paid
             FROM students s LEFT JOIN classes c ON c.id = s.class_id
             WHERE s.status = 'Active'"""
    params = []
    if query:
        sql += """ AND (s.first_name || ' ' || s.last_name LIKE ?
                    OR s.admission_number LIKE ?)"""
        params.extend([f"%{query}%", f"%{query}%"])
    sql += " ORDER BY (billed - paid) DESC, student_name"

    database = get_db()
    ledger = database.execute(sql, params).fetchall()
    totals = database.execute(
        """SELECT
             COALESCE((SELECT SUM(amount) FROM fee_invoices), 0) AS billed,
             COALESCE((SELECT SUM(amount) FROM payments), 0) AS paid,
             COALESCE((SELECT SUM(amount) FROM payments WHERE paid_on >= date('now', '-30 day')), 0) AS last_30_days"""
    ).fetchone()
    recent = database.execute(
        """SELECT p.*, s.first_name || ' ' || s.last_name AS student_name
           FROM payments p JOIN students s ON s.id = p.student_id
           ORDER BY p.paid_on DESC, p.id DESC LIMIT 8"""
    ).fetchall()
    return render_template(
        "finance/index.html", ledger=ledger, totals=totals, recent=recent, query=query
    )


@bp.route("/payments/new", methods=("GET", "POST"))
@roles_required("admin", "bursar")
def create_payment():
    database = get_db()
    selected_student = request.args.get("student_id", type=int) or request.form.get("student_id", type=int)
    students = database.execute(
        """SELECT id, admission_number, first_name, last_name
           FROM students WHERE status = 'Active' ORDER BY first_name, last_name"""
    ).fetchall()

    if request.method == "POST":
        method = request.form.get("method", "")
        reference = request.form.get("reference", "").strip() or None
        paid_on = request.form.get("paid_on", "")
        notes = request.form.get("notes", "").strip() or None
        try:
            amount = int(request.form.get("amount", ""))
        except ValueError:
            amount = 0

        error = None
        if selected_student is None:
            error = "Select a student."
        elif amount <= 0:
            error = "Enter an amount greater than zero."
        elif method not in ("M-PESA", "Cash", "Bank", "Cheque"):
            error = "Select a valid payment method."
        elif not paid_on:
            error = "Select the payment date."

        if error:
            flash(error, "error")
        else:
            cursor = database.execute(
                """INSERT INTO payments
                   (student_id, amount, method, reference, paid_on, notes, recorded_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (selected_student, amount, method, reference, paid_on, notes, g.user["id"]),
            )
            receipt = f"RCT-{setting('academic_year', str(date.today().year))}-{cursor.lastrowid:05d}"
            database.execute(
                "UPDATE payments SET receipt_number = ? WHERE id = ?",
                (receipt, cursor.lastrowid),
            )
            student = database.execute(
                "SELECT first_name, last_name FROM students WHERE id = ?", (selected_student,)
            ).fetchone()
            log_activity(
                "Payment recorded",
                f"{receipt} · {student['first_name']} {student['last_name']} · KES {amount:,}",
                g.user["id"],
            )
            database.commit()
            flash(f"Payment recorded. Receipt {receipt}", "success")
            return redirect(url_for("finance.receipt", payment_id=cursor.lastrowid))

    return render_template(
        "finance/payment_form.html",
        students=students,
        selected_student=selected_student,
        today=date.today().isoformat(),
    )


@bp.route("/invoices/new", methods=("GET", "POST"))
@roles_required("admin", "bursar")
def create_invoice():
    database = get_db()
    selected_student = request.args.get("student_id", type=int) or request.form.get("student_id", type=int)
    students = database.execute(
        """SELECT id, admission_number, first_name, last_name
           FROM students WHERE status = 'Active' ORDER BY first_name, last_name"""
    ).fetchall()

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "") or None
        try:
            amount = int(request.form.get("amount", ""))
            academic_year = int(request.form.get("academic_year", ""))
            term = int(request.form.get("term", ""))
        except ValueError:
            amount, academic_year, term = -1, 0, 0

        error = None
        if selected_student is None:
            error = "Select a student."
        elif not description:
            error = "Enter an invoice description."
        elif amount < 0:
            error = "Enter a valid amount."
        elif term not in (1, 2, 3):
            error = "Select a valid term."
        elif academic_year < 2020:
            error = "Enter a valid academic year."

        if error:
            flash(error, "error")
        else:
            database.execute(
                """INSERT INTO fee_invoices
                   (student_id, academic_year, term, description, amount, due_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (selected_student, academic_year, term, description, amount, due_date),
            )
            log_activity("Invoice raised", f"{description} · KES {amount:,}", g.user["id"])
            database.commit()
            flash("Invoice added to the student's account.", "success")
            return redirect(url_for("students.detail", student_id=selected_student))

    return render_template(
        "finance/invoice_form.html",
        students=students,
        selected_student=selected_student,
        current_year=setting("academic_year", str(date.today().year)),
        current_term=setting("current_term", "1"),
    )


@bp.get("/payments/<int:payment_id>/receipt")
@roles_required("admin", "bursar")
def receipt(payment_id):
    database = get_db()
    payment = database.execute(
        """SELECT p.*, s.admission_number,
                  s.first_name || ' ' || s.last_name AS student_name,
                  s.guardian_name, c.name AS class_name, u.full_name AS recorded_by_name
           FROM payments p
           JOIN students s ON s.id = p.student_id
           LEFT JOIN classes c ON c.id = s.class_id
           LEFT JOIN users u ON u.id = p.recorded_by
           WHERE p.id = ?""",
        (payment_id,),
    ).fetchone()
    if payment is None:
        return redirect(url_for("finance.index"))
    totals = database.execute(
        """SELECT
             COALESCE((SELECT SUM(amount) FROM fee_invoices WHERE student_id = ?), 0) AS billed,
             COALESCE((SELECT SUM(amount) FROM payments WHERE student_id = ?), 0) AS paid""",
        (payment["student_id"], payment["student_id"]),
    ).fetchone()
    return render_template("finance/receipt.html", payment=payment, totals=totals)
