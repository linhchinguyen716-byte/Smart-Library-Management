"""Nhóm chức năng: reservations. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

@app.route("/reservations", methods=["GET","POST"])
@login_required
def reservations():
    conn=db()
    if request.method == "POST":
        try:
            reader_id=int(request.form.get("reader_id",0))
            book_id=int(request.form.get("book_id",0))
            reader=conn.execute("SELECT id FROM readers WHERE id=?",(reader_id,)).fetchone()
            book=conn.execute("SELECT id,title,available FROM books WHERE id=?",(book_id,)).fetchone()
            dup=conn.execute("SELECT id FROM reservations WHERE reader_id=? AND book_id=? AND status='Chờ xử lý'",(reader_id,book_id)).fetchone()
            if not reader or not book:
                flash("Độc giả hoặc sách không tồn tại.","error")
            elif dup:
                flash("Độc giả đã đặt trước sách này.","error")
            else:
                conn.execute("INSERT INTO reservations(reader_id,book_id,reserved_at) VALUES(?,?,?)",(reader_id,book_id,datetime.now().isoformat(timespec="seconds")))
                log_action(conn,"Đặt trước",f"Độc giả #{reader_id} đặt sách {book['title']}")
                conn.commit()
                flash("Đã ghi nhận yêu cầu đặt trước sách.","success")
        except (ValueError,sqlite3.IntegrityError):
            flash("Dữ liệu đặt trước không hợp lệ.","error")
        finally:
            conn.close()
        return redirect(url_for("reservations"))
    rows=conn.execute("""SELECT r.*, b.title, b.available, d.name AS reader
                         FROM reservations r JOIN books b ON b.id=r.book_id
                         JOIN readers d ON d.id=r.reader_id ORDER BY r.id DESC""").fetchall()
    readers=conn.execute("SELECT id,name,code FROM readers ORDER BY name").fetchall()
    books=conn.execute("SELECT id,title,code,available FROM books ORDER BY title").fetchall()
    conn.close()
    return render_template("reservations.html",reservations=rows,readers=readers,books=books)


@app.post("/reservations/<int:id>/status")
@login_required
def reservation_status(id):
    status=request.form.get("status")
    if status not in ("Đã thông báo","Đã hủy"):
        flash("Trạng thái không hợp lệ.","error")
        return redirect(url_for("reservations"))
    conn=db()
    row=conn.execute("SELECT r.*, b.available FROM reservations r JOIN books b ON b.id=r.book_id WHERE r.id=?",(id,)).fetchone()
    if row and row["status"]=="Chờ xử lý":
        if status=="Đã thông báo" and row["available"]<1:
            flash("Sách vẫn đang hết, chưa thể thông báo có sách.","error")
        else:
            conn.execute("UPDATE reservations SET status=? WHERE id=?",(status,id))
            log_action(conn,"Đặt trước",f"Cập nhật yêu cầu #{id}: {status}")
            conn.commit()
            flash("Đã cập nhật yêu cầu.","success")
    else:
        flash("Yêu cầu không tồn tại hoặc đã xử lý.","error")
    conn.close()
    return redirect(url_for("reservations"))


@app.post("/reservations/<int:id>/complete")
@login_required
def complete_reservation(id):
    conn = db()
    row = conn.execute("""
        SELECT r.*, b.available, b.title, b.code AS book_code
        FROM reservations r JOIN books b ON b.id=r.book_id
        WHERE r.id=?
    """, (id,)).fetchone()

    if not row or row["status"] in ("Hoàn tất", "Đã hủy"):
        flash("Yêu cầu không tồn tại hoặc đã được xử lý.", "error")
    elif row["available"] < 1:
        flash(f"Ấn phẩm '{row['title']}' hiện không còn bản khả dụng nào để cho mượn.", "error")
    else:
        # 1. Trừ số lượng sách khả dụng trong kho
        conn.execute("UPDATE books SET available = available - 1 WHERE id = ?", (row["book_id"],))

        # 2. Tạo phiếu mượn sách chính thức
        loan_code = "PM" + datetime.now().strftime("%Y%m%d%H%M%S%f")[-12:]
        emp_id = session.get("employee_id")
        if not emp_id:
            emp = conn.execute("SELECT id FROM employees ORDER BY id LIMIT 1").fetchone()
            emp_id = emp["id"] if emp else 1

        today_str = date.today().isoformat()
        due_str = (date.today() + timedelta(days=14)).isoformat()

        conn.execute("""
            INSERT INTO loans(code, reader_id, employee_id, borrow_date, due_date, status)
            VALUES(?, ?, ?, ?, ?, 'Đang mượn')
        """, (loan_code, row["reader_id"], emp_id, today_str, due_str))

        loan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 3. Tạo chi tiết ấn phẩm mượn
        conn.execute("""
            INSERT INTO loan_items(loan_id, book_id, quantity)
            VALUES(?, ?, 1)
        """, (loan_id, row["book_id"]))

        # 4. Đánh dấu yêu cầu đặt trước đã hoàn tất
        conn.execute("UPDATE reservations SET status='Hoàn tất' WHERE id=?", (id,))

        log_action(conn, "Cho mượn", f"Hoàn tất cho mượn '{row['title']}' (Phiếu #{loan_code}) cho độc giả #{row['reader_id']} từ đơn đặt trước #{id}")
        conn.commit()
        flash(f"Đã hoàn tất cho mượn! Đã tạo phiếu mượn #{loan_code} và trừ 1 bản sách khỏi kho.", "success")
    conn.close()
    return redirect(url_for("reservations"))


