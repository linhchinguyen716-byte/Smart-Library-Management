"""Nhóm chức năng: people. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

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


