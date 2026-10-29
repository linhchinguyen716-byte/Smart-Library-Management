"""API Thống kê tổng quan, báo cáo và nhật ký hoạt động."""
from ..core import app, db
from .common import success, employee_only, rows


@app.get("/api/dashboard")
@employee_only
def api_dashboard():
    with db() as conn:
        stats = {
            "books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
            "copies": conn.execute("SELECT COALESCE(SUM(quantity),0) FROM books").fetchone()[0],
            "readers": conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0],
            "employees": conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0],
            "active_loans": conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn'").fetchone()[0],
            "overdue": conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn' AND due_date<date('now')").fetchone()[0],
            "reservations": conn.execute("SELECT COUNT(*) FROM reservations WHERE status='Chờ xử lý'").fetchone()[0],
        }
        popular = [
            dict(r) for r in conn.execute(
                "SELECT b.title,SUM(li.quantity) borrowed FROM loan_items li JOIN books b ON b.id=li.book_id GROUP BY b.id ORDER BY borrowed DESC LIMIT 6"
            )
        ]
    return success(stats=stats, popular=popular)


@app.get("/api/reports")
@employee_only
def api_reports():
    return success(
        categories=rows(
            "SELECT COALESCE(c.name,'Chưa phân loại') name,SUM(b.quantity) total FROM books b LEFT JOIN categories c ON c.id=b.category_id GROUP BY b.category_id ORDER BY total DESC"
        ),
        monthly=rows(
            "SELECT substr(borrow_date,1,7) month,COUNT(*) total FROM loans GROUP BY month ORDER BY month DESC LIMIT 12"
        ),
        popular=rows(
            "SELECT b.title,SUM(li.quantity) total FROM loan_items li JOIN books b ON b.id=li.book_id GROUP BY b.id ORDER BY total DESC LIMIT 10"
        ),
    )


@app.get("/api/activity")
@employee_only
def api_activity():
    return success(items=rows(
        "SELECT a.*,e.name employee FROM audit_logs a LEFT JOIN employees e ON e.id=a.employee_id ORDER BY a.id DESC LIMIT 100"
    ))
