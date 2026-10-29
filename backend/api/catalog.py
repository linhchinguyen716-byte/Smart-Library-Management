"""API Quản lý sách và thể loại (/api/books, /api/categories)."""
from ..core import app, db, request, session, sqlite3
from .common import success, fail, employee_only, rows, require


@app.get("/api/books")
def api_books():
    if not (session.get("employee_id") or session.get("reader_id")):
        return fail("Cần đăng nhập.", 401)
    term = request.args.get("q", "").strip()
    sql = "SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id"
    if term:
        sql += " WHERE b.code LIKE ? OR b.title LIKE ? OR b.author LIKE ?"
    sql += " ORDER BY b.id DESC"
    return success(items=rows(sql, tuple([f"%{term}%"] * 3) if term else ()))


@app.post("/api/books")
@employee_only
def api_add_book():
    try:
        d = require("code", "title", "author")
        qty = int(d.get("quantity", 1))
        year = int(d["year"]) if str(d.get("year", "")).strip() else None
        if qty < 1:
            return fail("Số lượng phải lớn hơn 0.")
        with db() as conn:
            conn.execute(
                "INSERT INTO books(code,title,author,publisher,year,category_id,quantity,available) VALUES(?,?,?,?,?,?,?,?)",
                (
                    d["code"].strip(),
                    d["title"].strip(),
                    d["author"].strip(),
                    d.get("publisher", "").strip(),
                    year,
                    int(d["category_id"]) if d.get("category_id") else None,
                    qty,
                    qty,
                )
            )
        return success(message="Đã thêm sách.")
    except sqlite3.IntegrityError:
        return fail("Mã sách trùng hoặc thể loại không hợp lệ.")
    except (ValueError, TypeError) as e:
        return fail("Dữ liệu sách không hợp lệ: " + str(e))


@app.put("/api/books/<int:id>")
@employee_only
def api_edit_book(id):
    try:
        d = require("code", "title", "author")
        qty = int(d.get("quantity", 0))
        with db() as conn:
            row = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
            if not row:
                return fail("Không tìm thấy sách.", 404)
            borrowed = row["quantity"] - row["available"]
            if qty < borrowed:
                return fail("Số lượng không thể ít hơn số sách đang được mượn.")
            conn.execute(
                "UPDATE books SET code=?,title=?,author=?,publisher=?,year=?,category_id=?,quantity=?,available=? WHERE id=?",
                (
                    d["code"],
                    d["title"],
                    d["author"],
                    d.get("publisher", ""),
                    int(d["year"]) if d.get("year") else None,
                    int(d["category_id"]) if d.get("category_id") else None,
                    qty,
                    qty - borrowed,
                    id,
                )
            )
        return success(message="Đã sửa sách.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Dữ liệu không hợp lệ hoặc trùng mã sách.")


@app.delete("/api/books/<int:id>")
@employee_only
def api_delete_book(id):
    try:
        with db() as conn:
            conn.execute("DELETE FROM books WHERE id=?", (id,))
        return success(message="Đã xóa sách.")
    except sqlite3.IntegrityError:
        return fail("Không thể xóa sách đã có lịch sử mượn hoặc đặt trước.")


@app.get("/api/categories")
@employee_only
def api_categories():
    return success(items=rows("SELECT * FROM categories ORDER BY name"))


@app.post("/api/categories")
@employee_only
def api_add_category():
    try:
        d = require("name")
        with db() as conn:
            conn.execute(
                "INSERT INTO categories(name,description) VALUES(?,?)",
                (d["name"].strip(), d.get("description", "").strip())
            )
        return success(message="Đã thêm thể loại.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Thể loại không hợp lệ hoặc đã có.")


@app.delete("/api/categories/<int:id>")
@employee_only
def api_delete_category(id):
    with db() as conn:
        conn.execute("DELETE FROM categories WHERE id=?", (id,))
    return success(message="Đã xóa thể loại.")
