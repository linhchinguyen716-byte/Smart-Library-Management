"""API Quản lý độc giả và nhân viên (/api/readers, /api/employees)."""
from ..core import app, db, sqlite3, generate_password_hash
from .common import success, fail, employee_only, role_admin, rows, require


@app.get("/api/readers")
@employee_only
def api_readers():
    return success(items=rows("SELECT * FROM readers ORDER BY id DESC"))


@app.post("/api/readers")
@employee_only
def api_add_reader():
    try:
        d = require("code", "name")
        with db() as conn:
            conn.execute(
                "INSERT INTO readers(code,name,dob,phone,email,address) VALUES(?,?,?,?,?,?)",
                tuple(d.get(k, "") for k in ("code", "name", "dob", "phone", "email", "address"))
            )
        return success(message="Đã thêm độc giả.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Mã độc giả trùng hoặc dữ liệu không hợp lệ.")


@app.put("/api/readers/<int:id>")
@employee_only
def api_edit_reader(id):
    try:
        d = require("code", "name")
        with db() as conn:
            conn.execute(
                "UPDATE readers SET code=?,name=?,dob=?,phone=?,email=?,address=? WHERE id=?",
                tuple(d.get(k, "") for k in ("code", "name", "dob", "phone", "email", "address")) + (id,)
            )
        return success(message="Đã cập nhật độc giả.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Dữ liệu độc giả không hợp lệ.")


@app.delete("/api/readers/<int:id>")
@employee_only
def api_delete_reader(id):
    try:
        with db() as conn:
            conn.execute("DELETE FROM readers WHERE id=?", (id,))
        return success(message="Đã xóa độc giả.")
    except sqlite3.IntegrityError:
        return fail("Không thể xóa độc giả có lịch sử mượn hoặc tài khoản.")


@app.get("/api/employees")
@role_admin
def api_employees():
    return success(items=rows("SELECT id,code,name,username,role FROM employees ORDER BY id DESC"))


@app.post("/api/employees")
@role_admin
def api_add_employee():
    try:
        d = require("code", "name", "username", "password", "role")
        with db() as conn:
            conn.execute(
                "INSERT INTO employees(code,name,username,password,role) VALUES(?,?,?,?,?)",
                (d["code"], d["name"], d["username"], generate_password_hash(d["password"]), d["role"])
            )
        return success(message="Đã thêm nhân viên.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Mã hoặc tên đăng nhập đã tồn tại.")
