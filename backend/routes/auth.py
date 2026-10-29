"""Nhóm chức năng: auth. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

@app.route("/login")
def login():
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = db()
        emp = conn.execute("SELECT * FROM employees WHERE username=?", (u,)).fetchone()
        if emp and password_matches(emp["password"], password):
            if not emp["password"].startswith(("scrypt:", "pbkdf2:")):
                conn.execute("UPDATE employees SET password=? WHERE id=?",
                             (generate_password_hash(password), emp["id"]))
                conn.commit()
            conn.close()
            session.clear()
            session["employee_id"] = emp["id"]
            session["employee_name"] = emp["name"]
            session["role"] = emp["role"]
            return redirect(url_for("dashboard"))
        conn.close()
        flash("Sai tài khoản hoặc mật khẩu.", "error")
    return render_template("login.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as conn:
            account = conn.execute("""SELECT a.*, r.name FROM reader_accounts a
                JOIN readers r ON r.id=a.reader_id WHERE a.username=?""", (username,)).fetchone()
        if account and check_password_hash(account["password_hash"], password):
            session.clear()
            session["reader_id"] = account["reader_id"]
            session["reader_name"] = account["name"]
            return redirect(url_for("user_home"))
        flash("Sai tài khoản hoặc mật khẩu độc giả.", "error")
    return render_template("user_login.html")


@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not name or len(username) < 3 or len(password) < 8:
            flash("Nhập tên, tài khoản từ 3 ký tự và mật khẩu từ 8 ký tự.", "error")
        else:
            try:
                with db() as conn:
                    code = "DG" + datetime.now().strftime("%Y%m%d%H%M%S%f")
                    cursor = conn.execute("INSERT INTO readers(code,name,email,phone) VALUES (?,?,?,?)",
                        (code, name, request.form.get("email", "").strip(), request.form.get("phone", "").strip()))
                    conn.execute("INSERT INTO reader_accounts(reader_id,username,password_hash) VALUES (?,?,?)",
                                 (cursor.lastrowid, username, generate_password_hash(password)))
                flash("Đăng ký thành công. Hãy đăng nhập.", "success")
                return redirect(url_for("user_login"))
            except sqlite3.IntegrityError:
                flash("Tên đăng nhập đã tồn tại.", "error")
    return render_template("user_register.html")


@app.get("/user")
@reader_required
def user_home():
    with db() as conn:
        books = conn.execute("""SELECT b.*, c.name AS category FROM books b
            LEFT JOIN categories c ON c.id=b.category_id ORDER BY b.title""").fetchall()
        reservations = conn.execute("""SELECT r.*, b.title FROM reservations r
            JOIN books b ON b.id=r.book_id WHERE r.reader_id=? ORDER BY r.id DESC""",
            (session["reader_id"],)).fetchall()
        loans = conn.execute("""SELECT l.*, GROUP_CONCAT(b.title, ', ') AS titles
            FROM loans l JOIN loan_items li ON li.loan_id=l.id
            JOIN books b ON b.id=li.book_id WHERE l.reader_id=?
            GROUP BY l.id ORDER BY l.id DESC""", (session["reader_id"],)).fetchall()
    return render_template("user_home.html", books=books, reservations=reservations, loans=loans)


@app.post("/user/reserve/<int:book_id>")
@reader_required
def user_reserve(book_id):
    with db() as conn:
        book = conn.execute("SELECT id FROM books WHERE id=?", (book_id,)).fetchone()
        duplicate = conn.execute("""SELECT id FROM reservations WHERE reader_id=? AND book_id=?
            AND status='Chờ xử lý'""", (session["reader_id"], book_id)).fetchone()
        if not book:
            abort(404)
        if duplicate:
            flash("Bạn đã đặt trước sách này.", "error")
        else:
            conn.execute("INSERT INTO reservations(reader_id,book_id,reserved_at) VALUES (?,?,?)",
                         (session["reader_id"], book_id, datetime.now().isoformat(timespec="seconds")))
            flash("Đã gửi yêu cầu đặt trước.", "success")
    return redirect(url_for("user_home"))


@app.get("/user/logout")
def user_logout():
    session.clear()
    return redirect(url_for("user_login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin_login"))


