from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import sqlite3
import csv
import io
import os
import qrcode
from qrcode.image.pil import PilImage
from datetime import timedelta
from flask import Response
from datetime import date, datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.environ.get("SECRET_KEY", "library-management-demo-change-before-deploy")
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library.db")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        publisher TEXT,
        year INTEGER,
        category_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 1,
        available INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS readers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        dob TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    );
    CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Nhân viên'
    );
    CREATE TABLE IF NOT EXISTS loans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        reader_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'Đang mượn',
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE RESTRICT
    );
    CREATE TABLE IF NOT EXISTS loan_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(loan_id) REFERENCES loans(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE RESTRICT
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        conn.executemany("INSERT INTO categories(name,description) VALUES(?,?)", [
            ("Văn học","Tác phẩm văn học"),
            ("Lập trình","Công nghệ và lập trình"),
            ("Kinh tế","Kinh tế, kinh doanh"),
            ("Ngoại ngữ","Sách học ngoại ngữ")
        ])
    if conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        conn.execute("INSERT INTO employees(code,name,username,password,role) VALUES(?,?,?,?,?)",
                     ("NV001","Quản trị viên","admin",generate_password_hash(os.environ.get("INITIAL_ADMIN_PASSWORD", secrets.token_urlsafe(16))),"Admin"))
    if conn.execute("SELECT COUNT(*) FROM readers").fetchone()[0] == 0:
        conn.executemany("INSERT INTO readers(code,name,phone,email,address) VALUES(?,?,?,?,?)", [
            ("DG001","Nguyễn Văn An","0900000001","an@example.com","Hà Nội"),
            ("DG002","Trần Minh Anh","0900000002","anh@example.com","Nam Định")
        ])
    if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        cats = {r["name"]:r["id"] for r in conn.execute("SELECT id,name FROM categories")}
        conn.executemany("""INSERT INTO books(code,title,author,publisher,year,category_id,quantity,available)
                            VALUES(?,?,?,?,?,?,?,?)""", [
            ("S001","Dế Mèn Phiêu Lưu Ký","Tô Hoài","Kim Đồng",1941,cats["Văn học"],5,5),
            ("S002","Python Crash Course","Eric Matthes","No Starch Press",2023,cats["Lập trình"],3,3),
            ("S003","Nhà Giả Kim","Paulo Coelho","NXB Hội Nhà Văn",1988,cats["Văn học"],4,4)
        ])
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS reservations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reader_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        reserved_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Chờ xử lý',
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE RESTRICT,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE RESTRICT
    );
    CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        action TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS reminders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL,
        employee_id INTEGER,
        reminder_date TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(loan_id) REFERENCES loans(id) ON DELETE CASCADE,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE SET NULL
    );
    CREATE INDEX IF NOT EXISTS idx_loans_due_status ON loans(status, due_date);
    CREATE INDEX IF NOT EXISTS idx_reservations_status_book ON reservations(status, book_id);
    """)
    conn.execute("""CREATE TABLE IF NOT EXISTS reader_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reader_id INTEGER NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        FOREIGN KEY(reader_id) REFERENCES readers(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

# Hàm decorator bắt buộc đăng nhập trước khi truy cập trang
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "employee_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject():
    return {"logged_in": "employee_id" in session, "employee_name": session.get("employee_name")}


def password_matches(stored, supplied):
    if stored.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored, supplied)
    return secrets.compare_digest(stored, supplied)  # Migrate legacy password on login.


def reader_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "reader_id" not in session:
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return wrapped


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

@app.route("/")
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

@app.route("/readers", methods=["GET","POST"])
@login_required
def readers():
    conn=db()
    if request.method=="POST":
        try:
            conn.execute("INSERT INTO readers(code,name,dob,phone,email,address) VALUES(?,?,?,?,?,?)",
                         (request.form["code"].strip(),request.form["name"].strip(),request.form.get("dob"),
                          request.form.get("phone","").strip(),request.form.get("email","").strip(),
                          request.form.get("address","").strip()))
            conn.commit(); flash("Đã thêm độc giả.","success")
        except sqlite3.IntegrityError: flash("Mã độc giả đã tồn tại.","error")
        conn.close(); return redirect(url_for("readers"))
    rows=conn.execute("SELECT * FROM readers ORDER BY id DESC").fetchall()
    conn.close(); return render_template("readers.html",readers=rows)

@app.post("/readers/delete/<int:id>")
@login_required
def delete_reader(id):
    conn=db()
    try:
        conn.execute("DELETE FROM readers WHERE id=?",(id,)); conn.commit(); flash("Đã xóa độc giả.","success")
    except sqlite3.IntegrityError: flash("Không thể xóa độc giả đã có lịch sử mượn.","error")
    conn.close(); return redirect(url_for("readers"))

@app.route("/employees", methods=["GET","POST"])
@login_required
def employees():
    if session.get("role")!="Admin":
        flash("Chỉ Admin được quản lý nhân viên.","error"); return redirect(url_for("dashboard"))
    conn=db()
    if request.method=="POST":
        try:
            conn.execute("INSERT INTO employees(code,name,username,password,role) VALUES(?,?,?,?,?)",
                         (request.form["code"],request.form["name"],request.form["username"],
                          generate_password_hash(request.form["password"]),request.form["role"]))
            conn.commit(); flash("Đã thêm nhân viên.","success")
        except sqlite3.IntegrityError: flash("Mã hoặc tài khoản đã tồn tại.","error")
        conn.close(); return redirect(url_for("employees"))
    rows=conn.execute("SELECT id,code,name,username,role FROM employees ORDER BY id DESC").fetchall()
    conn.close(); return render_template("employees.html",employees=rows)

@app.post("/employees/delete/<int:id>")
@login_required
def delete_employee(id):
    if session.get("role")!="Admin": return redirect(url_for("dashboard"))
    conn=db(); conn.execute("DELETE FROM employees WHERE id=?",(id,)); conn.commit(); conn.close()
    flash("Đã xóa nhân viên.","success"); return redirect(url_for("employees"))

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

@app.route("/reports")
@login_required
def reports():
    conn=db()
    category=conn.execute("""SELECT COALESCE(c.name,'Chưa phân loại') name,SUM(b.quantity) copies
                             FROM books b LEFT JOIN categories c ON c.id=b.category_id
                             GROUP BY b.category_id ORDER BY copies DESC""").fetchall()
    monthly=conn.execute("""SELECT substr(borrow_date,1,7) month,COUNT(*) total
                            FROM loans GROUP BY month ORDER BY month DESC LIMIT 12""").fetchall()
    popular=conn.execute("""SELECT b.title,SUM(li.quantity) total
                            FROM loan_items li JOIN books b ON b.id=li.book_id
                            GROUP BY b.id ORDER BY total DESC LIMIT 10""").fetchall()
    conn.close()
    chart_category={"labels":[x["name"] for x in category],"values":[x["copies"] for x in category]}
    months=list(reversed(monthly))
    chart_monthly={"labels":[x["month"] for x in months],"values":[x["total"] for x in months]}
    chart_popular={"labels":[x["title"] for x in popular],"values":[x["total"] for x in popular]}
    return render_template("reports.html",category=category,monthly=monthly,popular=popular,
                           chart_category=chart_category,chart_monthly=chart_monthly,chart_popular=chart_popular)

# Các tính năng bổ sung (giữ nguyên các tuyến cũ)
def log_action(conn, action, description):
    conn.execute("INSERT INTO audit_logs(employee_id,action,description,created_at) VALUES(?,?,?,?)",
                 (session.get("employee_id"), action, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

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

@app.get("/export/<kind>.csv")
@login_required
def export_csv(kind):
    queries={
        "books": ("SELECT code,title,author,publisher,year,quantity,available FROM books ORDER BY id",["Mã sách","Tên sách","Tác giả","Nhà xuất bản","Năm","Tổng số","Còn lại"]),
        "readers": ("SELECT code,name,dob,phone,email,address FROM readers ORDER BY id",["Mã độc giả","Họ tên","Ngày sinh","SĐT","Email","Địa chỉ"]),
        "loans": ("SELECT code,reader_id,borrow_date,due_date,return_date,status FROM loans ORDER BY id",["Mã phiếu","ID độc giả","Ngày mượn","Hạn trả","Ngày trả","Trạng thái"])
    }
    if kind not in queries:
        return "Không có loại báo cáo này",404
    query,heads=queries[kind]
    conn=db(); rows=conn.execute(query).fetchall();conn.close()
    buf=io.StringIO();buf.write("\ufeff")
    writer=csv.writer(buf);writer.writerow(heads)
    for r in rows: writer.writerow(list(r))
    return Response(buf.getvalue(),mimetype="text/csv; charset=utf-8",headers={"Content-Disposition":f"attachment; filename={kind}.csv"})

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

@app.route("/readers/edit/<int:id>",methods=["GET","POST"])
@login_required
def edit_reader(id):
    conn=db(); reader=conn.execute("SELECT * FROM readers WHERE id=?",(id,)).fetchone()
    if not reader: conn.close();return "Không tìm thấy độc giả",404
    if request.method=="POST":
        try:
            conn.execute("UPDATE readers SET code=?,name=?,dob=?,phone=?,email=?,address=? WHERE id=?",
                tuple(request.form.get(k,"").strip() for k in ("code","name","dob","phone","email","address"))+(id,))
            log_action(conn,"Chỉnh sửa độc giả",f"Độc giả #{id}")
            conn.commit();flash("Đã cập nhật độc giả.","success")
            conn.close();return redirect(url_for("readers"))
        except sqlite3.IntegrityError:flash("Mã độc giả đã tồn tại.","error")
        conn.close();return redirect(url_for("edit_reader",id=id))
    conn.close();return render_template("edit_reader.html",reader=reader)

@app.get("/activity")
@login_required
def activity():
    conn=db()
    rows=conn.execute("""SELECT a.*,e.name AS employee FROM audit_logs a
          LEFT JOIN employees e ON e.id=a.employee_id ORDER BY a.id DESC LIMIT 150""").fetchall()
    conn.close();return render_template("activity.html",logs=rows)

# QR dẫn đến trang thông tin đầu sách (không chứa dữ liệu độc giả)
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

@app.post("/reservations/<int:id>/complete")
@login_required
def complete_reservation(id):
    conn=db()
    row=conn.execute("SELECT * FROM reservations WHERE id=?", (id,)).fetchone()
    if not row or row["status"] != "Đã thông báo":
        flash("Chỉ hoàn tất yêu cầu đã thông báo.","error")
    else:
        conn.execute("UPDATE reservations SET status='Hoàn tất' WHERE id=?", (id,))
        log_action(conn,"Đặt trước",f"Hoàn tất yêu cầu #{id}")
        conn.commit()
        flash("Đã hoàn tất yêu cầu. Nếu độc giả mượn sách, hãy tạo phiếu mượn riêng.","success")
    conn.close()
    return redirect(url_for("reservations"))

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5001, debug=os.environ.get("FLASK_DEBUG") == "1")