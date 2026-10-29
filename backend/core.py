from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import sqlite3
import csv
import io
import os
import qrcode
from qrcode.image.pil import PilImage
from datetime import timedelta
from flask import Response
from datetime import date, datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.environ.get("SECRET_KEY", "library-management-demo-change-before-deploy")
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library.db")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        publisher TEXT,
        year INTEGER,
        category_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 1,
        available INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS readers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        dob TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    );
    CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Nhân viên'
    );
    CREATE TABLE IF NOT EXISTS loans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        reader_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'Đang mượn',
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE RESTRICT
    );
    CREATE TABLE IF NOT EXISTS loan_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(loan_id) REFERENCES loans(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE RESTRICT
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        conn.executemany("INSERT INTO categories(name,description) VALUES(?,?)", [
            ("Văn học","Tác phẩm văn học"),
            ("Lập trình","Công nghệ và lập trình"),
            ("Kinh tế","Kinh tế, kinh doanh"),
            ("Ngoại ngữ","Sách học ngoại ngữ")
        ])
    if conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        conn.execute("INSERT INTO employees(code,name,username,password,role) VALUES(?,?,?,?,?)",
                     ("NV001","Quản trị viên","admin",generate_password_hash(os.environ.get("INITIAL_ADMIN_PASSWORD", secrets.token_urlsafe(16))),"Admin"))
    if conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0] == 0:
        conn.executemany("INSERT INTO readers(code,name,phone,email,address) VALUES(?,?,?,?,?)", [
            ("DG001","Nguyễn Văn An","0900000001","an@example.com","Hà Nội"),
            ("DG002","Trần Minh Anh","0900000002","anh@example.com","Nam Định")
        ])
    if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        cats = {r["name"]:r["id"] for r in conn.execute("SELECT id,name FROM categories")}
        conn.executemany("""INSERT INTO books(code,title,author,publisher,year,category_id,quantity,available)
                            VALUES(?,?,?,?,?,?,?,?)""", [
            ("S001","Dế Mèn Phiêu Lưu Ký","Tô Hoài","Kim Đồng",1941,cats["Văn học"],5,5),
            ("S002","Python Crash Course","Eric Matthes","No Starch Press",2023,cats["Lập trình"],3,3),
            ("S003","Nhà Giả Kim","Paulo Coelho","NXB Hội Nhà Văn",1988,cats["Văn học"],4,4)
        ])
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS reservations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reader_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        reserved_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Chờ xử lý',
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE RESTRICT
    );
    CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        action TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS reminders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        employee_id INTEGER,
        reminder_date TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(loan_id) REFERENCES loans(id) ON DELETE CASCADE,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE SET NULL
    );
    CREATE INDEX IF NOT EXISTS idx_loans_due_status ON loans(status, due_date);
    CREATE INDEX IF NOT EXISTS idx_reservations_status_book ON reservations(status, book_id);
    """)
    conn.execute("""CREATE TABLE IF NOT EXISTS reader_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reader_id INTEGER NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "employee_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject():
    return {"logged_in": "employee_id" in session, "employee_name": session.get("employee_name")}


def password_matches(stored, supplied):
    if stored.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored, supplied)
    return secrets.compare_digest(stored, supplied)  # Migrate legacy password on login.


def reader_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "reader_id" not in session:
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return wrapped


def log_action(conn, action, description):
    conn.execute("INSERT INTO audit_logs(employee_id,action,description,created_at) VALUES(?,?,?,?)",
                 (session.get("employee_id"), action, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

