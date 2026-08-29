import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Default application configuration.

    Environment variables override deployment-sensitive values while sensible
    local defaults keep the project easy to run for contributors.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DATABASE = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "school.sqlite3"))
    SCHOOL_NAME = os.environ.get("SCHOOL_NAME", "ElimuPro Academy")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    AUTO_INIT_DB = True
