# ElimuPro

A fresh, practical foundation for a Kenyan school management system. This version is intentionally small, structured, and easy to extend: Flask handles server-rendered pages and authentication, while SQLite keeps local development simple.

## What is included

- Secure session authentication with CSRF protection
- Administrator, teacher, and bursar roles
- School overview with enrolment, attendance, capacity, and fee metrics
- Student directory with search and filters
- Student admission, profile, editing, and class placement
- Class directory and capacity management
- Fee invoices, student balances, payments, and printable receipts
- Activity audit trail
- Responsive interface with no frontend framework or CDN dependency
- Deterministic demo data and an automated test suite

The rebuild deliberately leaves attendance entry and academic assessment as the next modules instead of carrying forward the previous monolithic implementation.

## Technology

- Python 3.11+
- Flask 3
- SQLite
- Jinja templates
- Plain CSS and JavaScript
- Pytest

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

Open [http://localhost:8000](http://localhost:8000).

The app also creates and seeds the local database automatically when it is first started. Run `python seed.py` whenever you explicitly want to reset it to the demonstration dataset.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Administrator | `admin@school.local` | `ChangeMe123!` |
| Teacher | `teacher@school.local` | `Teacher123!` |
| Bursar | `bursar@school.local` | `Bursar123!` |

These accounts are for local development only. Change or remove them before deployment.

## Project structure

```text
.
├── app.py                         # Development entry point
├── seed.py                        # Reset and seed the local database
├── requirements.txt
├── school_system/
│   ├── __init__.py                # Application factory
│   ├── auth.py                    # Authentication blueprint
│   ├── dashboard.py               # Overview blueprint
│   ├── students.py                # Student records blueprint
│   ├── academics.py               # Classes blueprint
│   ├── finance.py                 # Invoices, payments, receipts
│   ├── db.py                      # SQLite connection, CLI, demo seed
│   ├── security.py                # Access control and CSRF helpers
│   ├── schema.sql
│   ├── static/
│   └── templates/
└── tests/
```

## Database commands

Reset to an empty schema:

```bash
flask --app app init-db
```

Reset and include demo records:

```bash
flask --app app init-db --with-demo
```

The local database is stored at `instance/school.sqlite3` and is ignored by Git.

## Run tests

```bash
pytest
```

GitHub Actions runs the same suite on every push and pull request.

## Configuration

Copy `.env.example` values into your deployment environment. Flask does not load `.env` without an additional package, so export them through your shell or hosting provider:

```bash
export SECRET_KEY="a-long-random-production-secret"
export DATABASE_PATH="/absolute/path/to/school.sqlite3"
export SESSION_COOKIE_SECURE=true
```

## Suggested roadmap

1. Attendance entry and daily summaries
2. Subjects, assessments, marks, and report cards
3. Staff profiles and teaching assignments
4. Configurable fee structures and bulk invoicing
5. Parent portal and notifications
6. PostgreSQL plus migrations for hosted deployments
7. Multi-school tenancy only after the single-school workflow is stable

## Production notes

- Set a unique `SECRET_KEY` and enable secure cookies behind HTTPS.
- Replace all demo credentials before using real data.
- Put the database on persistent, backed-up storage.
- Run Flask behind a production WSGI server such as Gunicorn.
- Review local privacy and retention requirements before storing learner data.
