"""API Xác thực phiên làm việc (Admin / Nhân viên & Độc giả)."""
from ..core import app, db, session, datetime, sqlite3, generate_password_hash, check_password_hash, password_matches
from .common import success, fail, body, require


@app.get("/api/session")
def api_session():
    if session.get("employee_id"):
        return success(user={
            "id": session["employee_id"],
            "name": session.get("employee_name"),
            "role": session.get("role"),
            "kind": "admin",
        })
    if session.get("reader_id"):
        return success(user={
            "id": session["reader_id"],
            "name": session.get("reader_name"),
            "role": "Độc giả",
            "kind": "reader",
        })
    return success(user=None)


@app.post("/api/auth/login")
def api_login():
    data = body()
    kind = data.get("kind")
    username = str(data.get("username", "")).strip()
    pwd = data.get("password", "")
    if kind == "admin":
        with db() as conn:
            user = conn.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchone()
            if not user or not password_matches(user["password"], pwd):
                return fail("Sai tài khoản hoặc mật khẩu.", 401)
            if not user["password"].startswith(("scrypt:", "pbkdf2:")):
                conn.execute(
                    "UPDATE employees SET password=? WHERE id=?",
                    (generate_password_hash(pwd), user["id"])
                )
            session.clear()
            session.update(employee_id=user["id"], employee_name=user["name"], role=user["role"])
        return api_session()
    if kind == "reader":
        with db() as conn:
            user = conn.execute(
                "SELECT a.*,r.name FROM reader_accounts a JOIN readers r ON r.id=a.reader_id WHERE a.username=?",
                (username,)
            ).fetchone()
        if not user or not check_password_hash(user["password_hash"], pwd):
            return fail("Sai tài khoản hoặc mật khẩu độc giả.", 401)
        session.clear()
        session.update(reader_id=user["reader_id"], reader_name=user["name"])
        return api_session()
    return fail("Loại tài khoản không hợp lệ.")


@app.post("/api/auth/register")
def api_register():
    try:
        data = require("name", "username", "password")
        if len(data["username"]) < 3 or len(data["password"]) < 8:
            return fail("Tên đăng nhập từ 3 ký tự, mật khẩu từ 8 ký tự.")
        with db() as conn:
            code = "DG" + datetime.now().strftime("%Y%m%d%H%M%S%f")
            cursor = conn.execute(
                "INSERT INTO readers(code,name,email,phone) VALUES (?,?,?,?)",
                (code, data["name"].strip(), data.get("email", "").strip(), data.get("phone", "").strip())
            )
            conn.execute(
                "INSERT INTO reader_accounts(reader_id,username,password_hash) VALUES (?,?,?)",
                (cursor.lastrowid, data["username"].strip(), generate_password_hash(data["password"]))
            )
        return success(message="Đăng ký thành công. Hãy đăng nhập.")
    except sqlite3.IntegrityError:
        return fail("Tên đăng nhập đã được sử dụng.")
    except ValueError as e:
        return fail(str(e))


@app.post("/api/auth/logout")
def api_logout():
    session.clear()
    return success(message="Đã đăng xuất.")
