"""Nhóm chức năng: catalog. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

@app.route("/categories", methods=["GET","POST"])
@login_required
def categories():
    conn=db()
    if request.method=="POST":
        try:
            conn.execute("INSERT INTO categories(name,description) VALUES(?,?)",
                         (request.form["name"].strip(),request.form.get("description","").strip()))
            conn.commit(); flash("Đã thêm thể loại.","success")
        except sqlite3.IntegrityError: flash("Tên thể loại đã tồn tại.","error")
        conn.close(); return redirect(url_for("categories"))
    rows=conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close(); return render_template("categories.html", categories=rows)


@app.post("/categories/delete/<int:id>")
@login_required
def delete_category(id):
    conn=db(); conn.execute("DELETE FROM categories WHERE id=?",(id,)); conn.commit(); conn.close()
    flash("Đã xóa thể loại.","success"); return redirect(url_for("categories"))


@app.route("/books", methods=["GET","POST"])
@login_required
def books():
    conn=db()
    if request.method=="POST":
        try:
            qty=max(1,int(request.form["quantity"]))
            conn.execute("""INSERT INTO books(code,title,author,publisher,year,category_id,quantity,available)
                            VALUES(?,?,?,?,?,?,?,?)""",
                         (request.form["code"].strip(),request.form["title"].strip(),request.form["author"].strip(),
                          request.form.get("publisher","").strip(),request.form.get("year") or None,
                          request.form.get("category_id") or None,qty,qty))
            conn.commit(); flash("Đã thêm sách.","success")
        except sqlite3.IntegrityError: flash("Mã sách đã tồn tại.","error")
        conn.close(); return redirect(url_for("books"))
    q=request.args.get("q","").strip()
    if q:
        rows=conn.execute("""SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id
                             WHERE b.code LIKE ? OR b.title LIKE ? OR b.author LIKE ? ORDER BY b.id DESC""",
                          (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    else:
        rows=conn.execute("""SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id
                             ORDER BY b.id DESC""").fetchall()
    cats=conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close(); return render_template("books.html",books=rows,categories=cats,q=q)


@app.post("/books/delete/<int:id>")
@login_required
def delete_book(id):
    conn=db()
    try:
        conn.execute("DELETE FROM books WHERE id=?",(id,)); conn.commit(); flash("Đã xóa sách.","success")
    except sqlite3.IntegrityError: flash("Không thể xóa sách đã có lịch sử mượn.","error")
    conn.close(); return redirect(url_for("books"))


@app.get("/catalog")
@login_required
def catalog():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", type=int)
    available_only = request.args.get("available") == "1"
    sql = """SELECT b.*, c.name AS category FROM books b
             LEFT JOIN categories c ON c.id=b.category_id WHERE 1=1"""
    params = []
    if q:
        sql += " AND (b.title LIKE ? OR b.author LIKE ? OR b.code LIKE ? OR b.publisher LIKE ?)"
        params.extend([f"%{q}%"]*4)
    if category:
        sql += " AND b.category_id=?"
        params.append(category)
    if available_only:
        sql += " AND b.available>0"
    sql += " ORDER BY b.title COLLATE NOCASE"
    with db() as conn:
        rows=conn.execute(sql,params).fetchall()
        cats=conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("catalog.html",books=rows,categories=cats,q=q,category=category,available_only=available_only)


@app.route("/books/edit/<int:id>",methods=["GET","POST"])
@login_required
def edit_book(id):
    conn=db(); book=conn.execute("SELECT * FROM books WHERE id=?",(id,)).fetchone()
    if not book: conn.close();return "Không tìm thấy sách",404
    if request.method=="POST":
        try:
            qty=int(request.form["quantity"])
            borrowed=book["quantity"]-book["available"]
            if qty<borrowed or qty<0:
                flash(f"Số lượng phải từ {borrowed} trở lên (đang được mượn).","error")
            else:
                conn.execute("""UPDATE books SET code=?,title=?,author=?,publisher=?,year=?,category_id=?,quantity=?,available=? WHERE id=?""",
                    (request.form["code"].strip(),request.form["title"].strip(),request.form["author"].strip(),request.form.get("publisher","").strip(),request.form.get("year") or None,request.form.get("category_id") or None,qty,qty-borrowed,id))
                log_action(conn,"Chỉnh sửa sách",f"Sách #{id}")
                conn.commit();flash("Đã cập nhật sách.","success")
                conn.close();return redirect(url_for("books"))
        except (sqlite3.IntegrityError,ValueError):
            flash("Dữ liệu không hợp lệ hoặc trùng mã sách.","error")
        conn.close();return redirect(url_for("edit_book",id=id))
    cats=conn.execute("SELECT * FROM categories ORDER BY name").fetchall();conn.close()
    return render_template("edit_book.html",book=book,categories=cats)


@app.get("/books/qr/<int:id>.png")
@login_required
def book_qr(id):
    with db() as conn:
        book = conn.execute("SELECT id FROM books WHERE id=?", (id,)).fetchone()
    if not book:
        abort(404)
    target = url_for("book_detail", id=id, _external=True)
    img = qrcode.make(target, image_factory=PilImage, box_size=8, border=3)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return Response(output.getvalue(), mimetype="image/png", headers={"Cache-Control":"no-store"})


@app.get("/books/view/<int:id>")
@login_required
def book_detail(id):
    with db() as conn:
        book = conn.execute("""SELECT b.*, c.name AS category FROM books b
            LEFT JOIN categories c ON c.id=b.category_id WHERE b.id=?""", (id,)).fetchone()
        if not book:
            abort(404)
        waiting = conn.execute("""SELECT COUNT(*) FROM reservations WHERE book_id=? AND status='Chờ xử lý'""", (id,)).fetchone()[0]
    return render_template("book_detail.html", book=book, waiting=waiting)


@app.get("/scan")
@login_required
def scan_books():
    return render_template("scan.html")


@app.post("/scan/find")
@login_required
def scan_find():
    code = request.form.get("code", "").strip()
    # Dùng mã sách khi quét bằng máy quét USB/nhập tay; QR có thể mở URL trực tiếp.
    with db() as conn:
        book = conn.execute("SELECT id FROM books WHERE code=? COLLATE NOCASE", (code,)).fetchone()
    if not book:
        flash("Không tìm thấy mã sách.", "error")
        return redirect(url_for("scan_books"))
    return redirect(url_for("book_detail", id=book["id"]))


