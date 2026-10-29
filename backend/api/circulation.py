"""API Lưu thông mượn/trả, đặt trước và cảnh báo nhắc hạn."""
from ..core import app, db, session, date, datetime, timedelta, sqlite3
from .common import success, fail, employee_only, rows, body, require


@app.get("/api/loans")
@employee_only
def api_loans():
    return success(items=rows("""
        SELECT l.*, r.name reader, e.name employee,
               GROUP_CONCAT(b.title || ' ×' || li.quantity, ', ') books
        FROM loans l
        JOIN readers r ON r.id=l.reader_id
        JOIN employees e ON e.id=l.employee_id
        JOIN loan_items li ON li.loan_id=l.id
        JOIN books b ON b.id=li.book_id
        GROUP BY l.id ORDER BY l.id DESC
    """))


@app.post("/api/loans")
@employee_only
def api_add_loan():
    try:
        d = require("reader_id", "book_id", "due_date")
        qty = int(d.get("quantity", 1))
        book_id = int(d["book_id"])
        reader_id = int(d["reader_id"])
        if qty < 1 or d["due_date"] < date.today().isoformat():
            return fail("Ngày trả hoặc số lượng không hợp lệ.")
        with db() as conn:
            reader = conn.execute("SELECT id FROM readers WHERE id=?", (reader_id,)).fetchone()
            if not reader:
                return fail("Độc giả không tồn tại.")
            updated = conn.execute(
                "UPDATE books SET available=available-? WHERE id=? AND available>=?",
                (qty, book_id, qty)
            )
            if updated.rowcount != 1:
                return fail("Sách không đủ số lượng khả dụng.")
            code = "PM" + datetime.now().strftime("%Y%m%d%H%M%S%f")
            cursor = conn.execute(
                "INSERT INTO loans(code,reader_id,employee_id,borrow_date,due_date) VALUES(?,?,?,?,?)",
                (code, reader_id, session["employee_id"], date.today().isoformat(), d["due_date"])
            )
            conn.execute(
                "INSERT INTO loan_items(loan_id,book_id,quantity) VALUES(?,?,?)",
                (cursor.lastrowid, book_id, qty)
            )
        return success(message="Đã lập phiếu mượn.")
    except (ValueError, sqlite3.IntegrityError):
        return fail("Thông tin phiếu mượn không hợp lệ.")


@app.post("/api/loans/<int:id>/return")
@employee_only
def api_return_loan(id):
    with db() as conn:
        loan = conn.execute("SELECT status FROM loans WHERE id=?", (id,)).fetchone()
        if not loan or loan["status"] != "Đang mượn":
            return fail("Phiếu không ở trạng thái đang mượn.")
        for x in conn.execute("SELECT book_id,quantity FROM loan_items WHERE loan_id=?", (id,)):
            conn.execute("UPDATE books SET available=available+? WHERE id=?", (x["quantity"], x["book_id"]))
        conn.execute("UPDATE loans SET status='Đã trả',return_date=? WHERE id=?", (date.today().isoformat(), id))
    return success(message="Đã nhận sách trả.")


@app.post("/api/loans/<int:id>/renew")
@employee_only
def api_renew_loan(id):
    with db() as conn:
        loan = conn.execute("SELECT status,due_date FROM loans WHERE id=?", (id,)).fetchone()
        if not loan or loan["status"] != "Đang mượn" or loan["due_date"] < date.today().isoformat():
            return fail("Phiếu không thể gia hạn.")
        due = (date.fromisoformat(loan["due_date"]) + timedelta(days=7)).isoformat()
        conn.execute("UPDATE loans SET due_date=? WHERE id=?", (due, id))
    return success(message="Đã gia hạn thêm 7 ngày.")


@app.get("/api/reservations")
@employee_only
def api_reservations():
    return success(items=rows("""
        SELECT r.*, b.title, d.name reader, b.available
        FROM reservations r
        JOIN books b ON b.id=r.book_id
        JOIN readers d ON d.id=r.reader_id
        ORDER BY r.id DESC
    """))


@app.post("/api/reservations/<int:id>/status")
@employee_only
def api_reservation_status(id):
    d = body()
    status = d.get("status")
    if status not in ("Đã thông báo", "Đã hủy", "Hoàn tất"):
        return fail("Trạng thái không hợp lệ.")
    with db() as conn:
        row = conn.execute(
            "SELECT r.status,b.available FROM reservations r JOIN books b ON b.id=r.book_id WHERE r.id=?",
            (id,)
        ).fetchone()
        if not row:
            return fail("Không tìm thấy yêu cầu.", 404)
        if status == "Hoàn tất" and row["status"] != "Đã thông báo":
            return fail("Cần thông báo trước khi hoàn tất.")
        if status == "Đã thông báo" and row["available"] < 1:
            return fail("Sách chưa có sẵn.")
        if row["status"] in ("Hoàn tất", "Đã hủy"):
            return fail("Yêu cầu đã xử lý.")
        conn.execute("UPDATE reservations SET status=? WHERE id=?", (status, id))
    return success(message="Đã cập nhật đặt trước.")


@app.get("/api/alerts")
@employee_only
def api_alerts():
    until = (date.today() + timedelta(days=3)).isoformat()
    return success(items=rows("""
        SELECT l.*, r.name reader, r.email, r.phone
        FROM loans l JOIN readers r ON r.id=l.reader_id
        WHERE l.status='Đang mượn' AND l.due_date<=?
        ORDER BY l.due_date
    """, (until,)))


@app.post("/api/alerts/<int:id>/mark")
@employee_only
def api_mark_reminder(id):
    with db() as conn:
        loan = conn.execute("SELECT status FROM loans WHERE id=?", (id,)).fetchone()
        if not loan or loan["status"] != "Đang mượn":
            return fail("Phiếu không còn đang mượn.")
        conn.execute(
            "INSERT INTO reminders(loan_id,employee_id,reminder_date,note) VALUES(?,?,?,?)",
            (id, session["employee_id"], datetime.now().isoformat(timespec="seconds"), body().get("note", "")[:300])
        )
    return success(message="Đã ghi nhận nhắc hạn (không gửi SMS/email tự động).")
