"""Nhóm chức năng: reports. Giữ nguyên endpoint để tương thích HTML cũ."""
from ..core import *

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


@app.get("/activity")
@login_required
def activity():
    conn=db()
    rows=conn.execute("""SELECT a.*,e.name AS employee FROM audit_logs a
          LEFT JOIN employees e ON e.id=a.employee_id ORDER BY a.id DESC LIMIT 150""").fetchall()
    conn.close();return render_template("activity.html",logs=rows)


