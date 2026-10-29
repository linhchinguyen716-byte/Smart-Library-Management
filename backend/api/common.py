"""Tiện ích dùng chung và bảo vệ CSRF/Origin cho JSON REST API."""
from functools import wraps
from urllib.parse import urlparse
from flask import jsonify
from ..core import app, db, request, session


def success(**data):
    return jsonify(data)


def fail(message, status=400):
    return jsonify(error=message), status


def employee_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("employee_id"):
            return fail("Vui lòng đăng nhập nhân viên.", 401)
        return func(*args, **kwargs)
    return wrapper


def reader_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("reader_id"):
            return fail("Vui lòng đăng nhập độc giả.", 401)
        return func(*args, **kwargs)
    return wrapper


def role_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("employee_id"):
            return fail("Cần đăng nhập.", 401)
        if session.get("role") != "Admin":
            return fail("Chỉ quản trị viên có quyền này.", 403)
        return func(*args, **kwargs)
    return wrapper


def rows(sql, params=()):
    with db() as conn:
        return [dict(x) for x in conn.execute(sql, params).fetchall()]


def body():
    return request.get_json(silent=True) or {}


def require(*fields):
    data = body()
    for field in fields:
        if not str(data.get(field, "")).strip():
            raise ValueError("Thiếu thông tin: " + field)
    return data


@app.before_request
def protect_json_writes():
    if request.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("Origin")
        if origin:
            parsed = urlparse(origin)
            allowed = {"127.0.0.1", "localhost"}
            if parsed.hostname not in allowed or parsed.port not in (5001, 5173):
                return fail("Origin không hợp lệ.", 403)
        if not request.is_json:
            return fail("Yêu cầu JSON.", 415)
