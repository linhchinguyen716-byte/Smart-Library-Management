"""API Cổng thông tin dành riêng cho Độc giả (/api/reader/*)."""
from ..core import app, db, session, datetime
from .common import success, fail, reader_only, rows


@app.get("/api/reader/home")
@reader_only
def api_reader_home():
    rid = session["reader_id"]
    return success(
        books=rows(
            "SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id ORDER BY b.title"
        ),
        reservations=rows(
            "SELECT r.*,b.title FROM reservations r JOIN books b ON b.id=r.book_id WHERE r.reader_id=? ORDER BY r.id DESC",
            (rid,)
        ),
        loans=rows(
            "SELECT l.*,GROUP_CONCAT(b.title,', ') titles FROM loans l JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id WHERE l.reader_id=? GROUP BY l.id ORDER BY l.id DESC",
            (rid,)
        ),
    )


@app.post("/api/reader/reserve/<int:book_id>")
@reader_only
def api_reader_reserve(book_id):
    with db() as conn:
        book = conn.execute("SELECT id FROM books WHERE id=?", (book_id,)).fetchone()
        if not book:
            return fail("Không tìm thấy sách.", 404)
        duplicate = conn.execute(
            "SELECT id FROM reservations WHERE reader_id=? AND book_id=? AND status='Chờ xử lý'",
            (session["reader_id"], book_id)
        ).fetchone()
        if duplicate:
            return fail("Bạn đã đặt trước sách này.")
        conn.execute(
            "INSERT INTO reservations(reader_id,book_id,reserved_at) VALUES(?,?,?)",
            (session["reader_id"], book_id, datetime.now().isoformat(timespec="seconds"))
        )
    return success(message="Đã gửi yêu cầu đặt sách.")
