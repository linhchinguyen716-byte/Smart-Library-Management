"""Nhóm chức năng: dashboard. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *


@app.route("/admin")
@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    stats = {
        "books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "copies": conn.execute("SELECT COALESCE(SUM(quantity),0) FROM books").fetchone()[0],
        "readers": conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0],
        "employees": conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0],
        "active_loans": conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn'").fetchone()[0],
        "overdue": conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn' AND due_date < date('now')").fetchone()[0]
    }
    popular = conn.execute("""
      SELECT b.title, SUM(li.quantity) borrowed
      FROM loan_items li JOIN books b ON b.id=li.book_id
      GROUP BY li.book_id ORDER BY borrowed DESC LIMIT 5
    """).fetchall()
    conn.close()
    return render_template("dashboard.html", stats=stats, popular=popular)
