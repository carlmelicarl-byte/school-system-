from datetime import datetime
from pathlib import Path

from flask import Flask, abort, render_template, request

from .config import Config


def create_app(test_config=None):
    """Application factory used by the server, CLI, and test suite."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    from . import db
    from .security import csrf_token, validate_csrf

    db.init_app(app)

    if app.config.get("AUTO_INIT_DB") and not Path(app.config["DATABASE"]).exists():
        with app.app_context():
            db.init_db()
            db.seed_demo()

    @app.before_request
    def protect_unsafe_requests():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not validate_csrf():
            abort(400, description="The form expired. Refresh the page and try again.")

    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": csrf_token,
            "school_name": db.setting("school_name", app.config["SCHOOL_NAME"]),
            "school_motto": db.setting("school_motto", "Learn. Lead. Serve."),
            "academic_year": db.setting("academic_year", str(datetime.now().year)),
            "current_term": db.setting("current_term", "1"),
        }

    @app.template_filter("money")
    def money_filter(value):
        return f"KES {int(value or 0):,}"

    @app.template_filter("pretty_date")
    def pretty_date_filter(value):
        if not value:
            return "—"
        try:
            return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
        except ValueError:
            return value

    from .auth import bp as auth_bp
    from .dashboard import bp as dashboard_bp
    from .students import bp as students_bp
    from .academics import bp as academics_bp
    from .finance import bp as finance_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(academics_bp)
    app.register_blueprint(finance_bp)

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500

    return app
