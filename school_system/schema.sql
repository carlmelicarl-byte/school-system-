PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS activity_log;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS fee_invoices;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS settings;

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'bursar')),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 12),
    stream TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 40 CHECK (capacity > 0),
    class_teacher TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK (gender IN ('Female', 'Male', 'Other')),
    date_of_birth TEXT,
    joined_on TEXT NOT NULL,
    guardian_name TEXT NOT NULL,
    guardian_phone TEXT NOT NULL,
    class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'Graduated', 'Transferred', 'Inactive')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_name ON students(last_name, first_name);
CREATE INDEX idx_students_class ON students(class_id);

CREATE TABLE fee_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year INTEGER NOT NULL,
    term INTEGER NOT NULL CHECK (term BETWEEN 1 AND 3),
    description TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 0),
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoices_student ON fee_invoices(student_id);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number TEXT UNIQUE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
    amount INTEGER NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL CHECK (method IN ('M-PESA', 'Cash', 'Bank', 'Cheque')),
    reference TEXT,
    paid_on TEXT NOT NULL,
    notes TEXT,
    recorded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_student ON payments(student_id);
CREATE INDEX idx_payments_date ON payments(paid_on);

CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Present', 'Absent', 'Late', 'Excused')),
    UNIQUE(student_id, attendance_date)
);

CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
