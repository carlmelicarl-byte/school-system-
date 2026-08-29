from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db
from .security import is_safe_redirect


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            """SELECT id, full_name, email, role, active
               FROM users WHERE id = ?""",
            (user_id,),
        ).fetchone()
        if g.user is not None and not g.user["active"]:
            session.clear()
            g.user = None


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE email = ? AND active = 1", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("The email or password is incorrect.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = request.form.get("remember") == "on"
            next_url = request.args.get("next")
            if is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
