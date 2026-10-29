"""Nhóm chức năng: alerts. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

@app.get("/alerts")
@login_required
def alerts():
    today=date.today().isoformat()
    until=(date.today()+timedelta(days=3)).isoformat()
    conn=db()
    due=conn.execute("""SELECT l.*,r.name AS reader,r.phone,r.email,
             (SELECT COUNT(*) FROM reminders m WHERE m.loan_id=l.id) AS reminder_count,
             (SELECT MAX(m.reminder_date) FROM reminders m WHERE m.loan_id=l.id) AS last_reminder,
             GROUP_CONCAT(b.title, ', ') AS books
             FROM loans l JOIN readers r ON r.id=l.reader_id
             JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id
             WHERE l.status='Đang mượn' AND l.due_date<=?
             GROUP BY l.id ORDER BY l.due_date""",(until,)).fetchall()
    waiting=conn.execute("""SELECT r.*,b.title,b.available,d.name AS reader
          FROM reservations r JOIN books b ON b.id=r.book_id
          JOIN readers d ON d.id=r.reader_id
          WHERE r.status='Chờ xử lý' AND b.available>0 ORDER BY r.reserved_at""").fetchall()
    conn.close()
    return render_template("alerts.html",due=due,waiting=waiting,today=today)


@app.post("/reminders/<int:id>/mark")
@login_required
def mark_reminder(id):
    note = request.form.get("note", "").strip()[:300]
    conn = db()
    loan = conn.execute("SELECT id,code,status FROM loans WHERE id=?", (id,)).fetchone()
    if not loan or loan["status"] != "Đang mượn":
        conn.close()
        flash("Chỉ ghi nhận nhắc hạn với phiếu đang mượn.", "error")
    else:
        conn.execute("INSERT INTO reminders(loan_id,employee_id,reminder_date,note) VALUES(?,?,?,?)",
                     (id,session.get("employee_id"),datetime.now().isoformat(timespec="seconds"),note))
        log_action(conn,"Nhắc hạn",f"Đã ghi nhận nhắc hạn phiếu {loan['code']}")
        conn.commit()
        conn.close()
        flash("Đã lưu lịch sử nhắc hạn. Chức năng này không tự gửi email/SMS.", "success")
    return redirect(url_for("alerts"))


@app.get("/reminders")
@login_required
def reminder_history():
    with db() as conn:
        rows = conn.execute("""SELECT m.*,l.code AS loan_code,r.name AS reader,e.name AS employee
           FROM reminders m JOIN loans l ON l.id=m.loan_id JOIN readers r ON r.id=l.reader_id
           LEFT JOIN employees e ON e.id=m.employee_id ORDER BY m.id DESC LIMIT 200""").fetchall()
    return render_template("reminders.html", reminders=rows)


