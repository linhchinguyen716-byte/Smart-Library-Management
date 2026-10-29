"""Nhóm chức năng: loans. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

@app.route("/loans", methods=["GET","POST"])
@login_required
def loans():
    conn=db()
    if request.method=="POST":
        reader_id=int(request.form["reader_id"]); book_id=int(request.form["book_id"])
        due=request.form["due_date"]; qty=max(1,int(request.form.get("quantity",1)))
        book=conn.execute("SELECT * FROM books WHERE id=?",(book_id,)).fetchone()
        if not book or book["available"] < qty:
            flash("Số lượng sách khả dụng không đủ.","error")
        elif not due:
            flash("Vui lòng nhập hạn trả.","error")
        else:
            code="PM"+datetime.now().strftime("%Y%m%d%H%M%S%f")[-12:]
            conn.execute("""INSERT INTO loans(code,reader_id,employee_id,borrow_date,due_date)
                            VALUES(?,?,?,?,?)""",
                         (code,reader_id,session["employee_id"],date.today().isoformat(),due))
            loan_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO loan_items(loan_id,book_id,quantity) VALUES(?,?,?)",(loan_id,book_id,qty))
            conn.execute("UPDATE books SET available=available-? WHERE id=?",(qty,book_id))
            conn.commit(); flash("Đã tạo phiếu mượn.","success")
        conn.close(); return redirect(url_for("loans"))
    rows=conn.execute("""
      SELECT l.*,r.name reader,e.name employee,
             GROUP_CONCAT(b.title || ' x' || li.quantity, ', ') books
      FROM loans l JOIN readers r ON r.id=l.reader_id JOIN employees e ON e.id=l.employee_id
      JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id
      GROUP BY l.id ORDER BY l.id DESC
    """).fetchall()
    books=conn.execute("SELECT * FROM books WHERE available>0 ORDER BY title").fetchall()
    readers=conn.execute("SELECT * FROM readers ORDER BY name").fetchall()
    conn.close(); return render_template("loans.html",loans=rows,books=books,readers=readers,today=date.today().isoformat())


@app.post("/loans/return/<int:id>")
@login_required
def return_loan(id):
    conn=db()
    loan=conn.execute("SELECT * FROM loans WHERE id=?",(id,)).fetchone()
    if loan and loan["status"]=="Đang mượn":
        items=conn.execute("SELECT * FROM loan_items WHERE loan_id=?",(id,)).fetchall()
        for x in items:
            conn.execute("UPDATE books SET available=available+? WHERE id=?",(x["quantity"],x["book_id"]))
        conn.execute("UPDATE loans SET status='Đã trả',return_date=? WHERE id=?",(date.today().isoformat(),id))
        conn.commit(); flash("Đã ghi nhận trả sách.","success")
    conn.close(); return redirect(url_for("loans"))


@app.route("/overdue")
@login_required
def overdue():
    conn=db()
    rows=conn.execute("""
      SELECT l.*,r.name reader,
             GROUP_CONCAT(b.title || ' x' || li.quantity, ', ') books,
             CAST(julianday(date('now'))-julianday(l.due_date) AS INTEGER) days
      FROM loans l JOIN readers r ON r.id=l.reader_id
      JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id
      WHERE l.status='Đang mượn' AND l.due_date < date('now')
      GROUP BY l.id ORDER BY days DESC
    """).fetchall()
    conn.close(); return render_template("overdue.html",loans=rows)


@app.post("/loans/renew/<int:id>")
@login_required
def renew_loan(id):
    conn=db()
    loan=conn.execute("SELECT * FROM loans WHERE id=?",(id,)).fetchone()
    if not loan or loan["status"]!="Đang mượn":
        flash("Chỉ có thể gia hạn phiếu đang mượn.","error")
    elif loan["due_date"] < date.today().isoformat():
        flash("Phiếu đã quá hạn, vui lòng liên hệ thủ thư.","error")
    else:
        current=date.fromisoformat(loan["due_date"])
        new_due=current+timedelta(days=7)
        conn.execute("UPDATE loans SET due_date=? WHERE id=?",(new_due.isoformat(),id))
        log_action(conn,"Gia hạn",f"Phiếu {loan['code']} đến {new_due.isoformat()}")
        conn.commit()
        flash("Đã gia hạn thêm 7 ngày.","success")
    conn.close()
    return redirect(url_for("loans"))


@app.get("/history")
@login_required
def history():
    q=request.args.get("q","").strip()
    conn=db()
    rows=conn.execute("""SELECT l.*,d.name AS reader,e.name AS employee,
             GROUP_CONCAT(b.title || ' x' || li.quantity, ', ') AS books
             FROM loans l JOIN readers d ON d.id=l.reader_id
             JOIN employees e ON e.id=l.employee_id
             JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id
             WHERE (d.name LIKE ? OR d.code LIKE ? OR l.code LIKE ?)
             GROUP BY l.id ORDER BY l.id DESC""",(f"%{q}%",)*3).fetchall()
    conn.close()
    return render_template("history.html",loans=rows,q=q)


