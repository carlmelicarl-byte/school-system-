#!/usr/bin/env python3
"""Reset the local database and load development demonstration data."""

from school_system import create_app
from school_system.db import init_db, seed_demo


if __name__ == "__main__":
    app = create_app({"AUTO_INIT_DB": False})
    with app.app_context():
        init_db()
        seed_demo()
    print("Fresh demo database created in instance/school.sqlite3")
