"""Middleware xác thực, kiểm tra mật khẩu và ghi nhật ký thao tác (Audit Log)."""
from datetime import datetime
from functools import wraps
import secrets
from flask import redirect, session, url_for
from werkzeug.security import check_password_hash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "employee_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def reader_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "reader_id" not in session:
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return wrapped


def password_matches(stored, supplied):
    if stored.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored, supplied)
    return secrets.compare_digest(stored, supplied)  # Migrate legacy password on login.


def log_action(conn, action, description):
    conn.execute(
        "INSERT INTO audit_logs(employee_id,action,description,created_at) VALUES(?,?,?,?)",
        (session.get("employee_id"), action, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
