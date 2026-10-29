"""JSON API cho React. Session Flask dùng chung cho cả hai giao diện."""
from ..core import app, db, session, request, generate_password_hash, check_password_hash, password_matches, datetime, date, timedelta, sqlite3, os
from flask import jsonify
from functools import wraps


def success(**data): return jsonify(data)
def fail(message, status=400): return jsonify(error=message), status

def employee_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('employee_id'): return fail('Vui lòng đăng nhập nhân viên.', 401)
        return func(*args, **kwargs)
    return wrapper

def reader_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('reader_id'): return fail('Vui lòng đăng nhập độc giả.', 401)
        return func(*args, **kwargs)
    return wrapper

def role_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('employee_id'): return fail('Cần đăng nhập.', 401)
        if session.get('role') != 'Admin': return fail('Chỉ quản trị viên có quyền này.', 403)
        return func(*args, **kwargs)
    return wrapper

def rows(sql, params=()):
    with db() as conn: return [dict(x) for x in conn.execute(sql, params).fetchall()]

def body(): return request.get_json(silent=True) or {}

def require(*fields):
    data=body()
    for field in fields:
        if not str(data.get(field, '')).strip(): raise ValueError('Thiếu thông tin: '+field)
    return data

@app.before_request
def protect_json_writes():
    if request.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE'):
        # Same-origin hoặc Vite development proxy; chặn cross-origin browser writes.
        origin=request.headers.get('Origin')
        if origin:
            from urllib.parse import urlparse
            parsed=urlparse(origin)
            allowed={'127.0.0.1','localhost'}
            if parsed.hostname not in allowed or parsed.port not in (5001,5173):
                return fail('Origin không hợp lệ.',403)
        if not request.is_json: return fail('Yêu cầu JSON.',415)

@app.get('/api/session')
def api_session():
    if session.get('employee_id'):
        return success(user={'id':session['employee_id'],'name':session.get('employee_name'),'role':session.get('role'),'kind':'admin'})
    if session.get('reader_id'):
        return success(user={'id':session['reader_id'],'name':session.get('reader_name'),'role':'Độc giả','kind':'reader'})
    return success(user=None)

@app.post('/api/auth/login')
def api_login():
    data=body(); kind=data.get('kind'); username=str(data.get('username','')).strip(); pwd=data.get('password','')
    if kind=='admin':
        with db() as conn:
            user=conn.execute('SELECT * FROM employees WHERE username=?',(username,)).fetchone()
            if not user or not password_matches(user['password'],pwd): return fail('Sai tài khoản hoặc mật khẩu.',401)
            if not user['password'].startswith(('scrypt:','pbkdf2:')):
                conn.execute('UPDATE employees SET password=? WHERE id=?',(generate_password_hash(pwd),user['id']))
            session.clear();session.update(employee_id=user['id'],employee_name=user['name'],role=user['role'])
        return api_session()
    if kind=='reader':
        with db() as conn:
            user=conn.execute('SELECT a.*,r.name FROM reader_accounts a JOIN readers r ON r.id=a.reader_id WHERE a.username=?',(username,)).fetchone()
        if not user or not check_password_hash(user['password_hash'],pwd): return fail('Sai tài khoản hoặc mật khẩu độc giả.',401)
        session.clear();session.update(reader_id=user['reader_id'],reader_name=user['name'])
        return api_session()
    return fail('Loại tài khoản không hợp lệ.')

@app.post('/api/auth/register')
def api_register():
    try:
        data=require('name','username','password')
        if len(data['username'])<3 or len(data['password'])<8:return fail('Tên đăng nhập từ 3 ký tự, mật khẩu từ 8 ký tự.')
        with db() as conn:
            code='DG'+datetime.now().strftime('%Y%m%d%H%M%S%f')
            cursor=conn.execute('INSERT INTO readers(code,name,email,phone) VALUES (?,?,?,?)',(code,data['name'].strip(),data.get('email','').strip(),data.get('phone','').strip()))
            conn.execute('INSERT INTO reader_accounts(reader_id,username,password_hash) VALUES (?,?,?)',(cursor.lastrowid,data['username'].strip(),generate_password_hash(data['password'])))
        return success(message='Đăng ký thành công. Hãy đăng nhập.')
    except sqlite3.IntegrityError: return fail('Tên đăng nhập đã được sử dụng.')
    except ValueError as e:return fail(str(e))

@app.post('/api/auth/logout')
def api_logout():session.clear();return success(message='Đã đăng xuất.')

@app.get('/api/dashboard')
@employee_only
def api_dashboard():
    with db() as conn:
        stats={
          'books':conn.execute('SELECT COUNT(*) FROM books').fetchone()[0],
          'copies':conn.execute('SELECT COALESCE(SUM(quantity),0) FROM books').fetchone()[0],
          'readers':conn.execute('SELECT COUNT(*) FROM readers').fetchone()[0],
          'employees':conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0],
          'active_loans':conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn'").fetchone()[0],
          'overdue':conn.execute("SELECT COUNT(*) FROM loans WHERE status='Đang mượn' AND due_date<date('now')").fetchone()[0],
          'reservations':conn.execute("SELECT COUNT(*) FROM reservations WHERE status='Chờ xử lý'").fetchone()[0]}
        popular=[dict(r) for r in conn.execute('SELECT b.title,SUM(li.quantity) borrowed FROM loan_items li JOIN books b ON b.id=li.book_id GROUP BY b.id ORDER BY borrowed DESC LIMIT 6')]
    return success(stats=stats,popular=popular)

@app.get('/api/books')
def api_books():
    if not (session.get('employee_id') or session.get('reader_id')):return fail('Cần đăng nhập.',401)
    term=request.args.get('q','').strip()
    sql='SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id'
    if term:sql+=' WHERE b.code LIKE ? OR b.title LIKE ? OR b.author LIKE ?'
    sql+=' ORDER BY b.id DESC'
    return success(items=rows(sql,tuple([f'%{term}%']*3) if term else ()))

@app.post('/api/books')
@employee_only
def api_add_book():
    try:
        d=require('code','title','author')
        qty=int(d.get('quantity',1));year=int(d['year']) if str(d.get('year','')).strip() else None
        if qty<1:return fail('Số lượng phải lớn hơn 0.')
        with db() as conn:
            conn.execute('INSERT INTO books(code,title,author,publisher,year,category_id,quantity,available) VALUES(?,?,?,?,?,?,?,?)',
                (d['code'].strip(),d['title'].strip(),d['author'].strip(),d.get('publisher','').strip(),year,int(d['category_id']) if d.get('category_id') else None,qty,qty))
        return success(message='Đã thêm sách.')
    except sqlite3.IntegrityError:return fail('Mã sách trùng hoặc thể loại không hợp lệ.')
    except (ValueError,TypeError) as e:return fail('Dữ liệu sách không hợp lệ: '+str(e))

@app.put('/api/books/<int:id>')
@employee_only
def api_edit_book(id):
    try:
        d=require('code','title','author');qty=int(d.get('quantity',0))
        with db() as conn:
            row=conn.execute('SELECT * FROM books WHERE id=?',(id,)).fetchone()
            if not row:return fail('Không tìm thấy sách.',404)
            borrowed=row['quantity']-row['available']
            if qty<borrowed:return fail('Số lượng không thể ít hơn số sách đang được mượn.')
            conn.execute('UPDATE books SET code=?,title=?,author=?,publisher=?,year=?,category_id=?,quantity=?,available=? WHERE id=?',
                (d['code'],d['title'],d['author'],d.get('publisher',''),int(d['year']) if d.get('year') else None,int(d['category_id']) if d.get('category_id') else None,qty,qty-borrowed,id))
        return success(message='Đã sửa sách.')
    except (ValueError,sqlite3.IntegrityError):return fail('Dữ liệu không hợp lệ hoặc trùng mã sách.')

@app.delete('/api/books/<int:id>')
@employee_only
def api_delete_book(id):
    try:
        with db() as conn:conn.execute('DELETE FROM books WHERE id=?',(id,))
        return success(message='Đã xóa sách.')
    except sqlite3.IntegrityError:return fail('Không thể xóa sách đã có lịch sử mượn hoặc đặt trước.')

@app.get('/api/categories')
@employee_only
def api_categories():return success(items=rows('SELECT * FROM categories ORDER BY name'))

@app.post('/api/categories')
@employee_only
def api_add_category():
    try:
        d=require('name')
        with db() as conn:conn.execute('INSERT INTO categories(name,description) VALUES(?,?)',(d['name'].strip(),d.get('description','').strip()))
        return success(message='Đã thêm thể loại.')
    except (ValueError,sqlite3.IntegrityError):return fail('Thể loại không hợp lệ hoặc đã có.')

@app.delete('/api/categories/<int:id>')
@employee_only
def api_delete_category(id):
    with db() as conn:conn.execute('DELETE FROM categories WHERE id=?',(id,))
    return success(message='Đã xóa thể loại.')

@app.get('/api/readers')
@employee_only
def api_readers():return success(items=rows('SELECT * FROM readers ORDER BY id DESC'))

@app.post('/api/readers')
@employee_only
def api_add_reader():
    try:
        d=require('code','name')
        with db() as conn:conn.execute('INSERT INTO readers(code,name,dob,phone,email,address) VALUES(?,?,?,?,?,?)',tuple(d.get(k,'') for k in ('code','name','dob','phone','email','address')))
        return success(message='Đã thêm độc giả.')
    except (ValueError,sqlite3.IntegrityError):return fail('Mã độc giả trùng hoặc dữ liệu không hợp lệ.')

@app.put('/api/readers/<int:id>')
@employee_only
def api_edit_reader(id):
    try:
        d=require('code','name')
        with db() as conn:conn.execute('UPDATE readers SET code=?,name=?,dob=?,phone=?,email=?,address=? WHERE id=?',tuple(d.get(k,'') for k in ('code','name','dob','phone','email','address'))+(id,))
        return success(message='Đã cập nhật độc giả.')
    except (ValueError,sqlite3.IntegrityError):return fail('Dữ liệu độc giả không hợp lệ.')

@app.delete('/api/readers/<int:id>')
@employee_only
def api_delete_reader(id):
    try:
        with db() as conn:conn.execute('DELETE FROM readers WHERE id=?',(id,))
        return success(message='Đã xóa độc giả.')
    except sqlite3.IntegrityError:return fail('Không thể xóa độc giả có lịch sử mượn hoặc tài khoản.')

@app.get('/api/employees')
@role_admin
def api_employees():return success(items=rows('SELECT id,code,name,username,role FROM employees ORDER BY id DESC'))

@app.post('/api/employees')
@role_admin
def api_add_employee():
    try:
        d=require('code','name','username','password','role')
        with db() as conn:conn.execute('INSERT INTO employees(code,name,username,password,role) VALUES(?,?,?,?,?)',(d['code'],d['name'],d['username'],generate_password_hash(d['password']),d['role']))
        return success(message='Đã thêm nhân viên.')
    except (ValueError,sqlite3.IntegrityError):return fail('Mã hoặc tên đăng nhập đã tồn tại.')

@app.get('/api/loans')
@employee_only
def api_loans():
    return success(items=rows("""SELECT l.*,r.name reader,e.name employee,GROUP_CONCAT(b.title||' ×'||li.quantity,', ') books FROM loans l JOIN readers r ON r.id=l.reader_id JOIN employees e ON e.id=l.employee_id JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id GROUP BY l.id ORDER BY l.id DESC"""))

@app.post('/api/loans')
@employee_only
def api_add_loan():
    try:
        d=require('reader_id','book_id','due_date');qty=int(d.get('quantity',1)); book_id=int(d['book_id']);reader_id=int(d['reader_id'])
        if qty<1 or d['due_date']<date.today().isoformat():return fail('Ngày trả hoặc số lượng không hợp lệ.')
        with db() as conn:
            reader=conn.execute('SELECT id FROM readers WHERE id=?',(reader_id,)).fetchone()
            if not reader:return fail('Độc giả không tồn tại.')
            updated=conn.execute('UPDATE books SET available=available-? WHERE id=? AND available>=?',(qty,book_id,qty))
            if updated.rowcount!=1:return fail('Sách không đủ số lượng khả dụng.')
            code='PM'+datetime.now().strftime('%Y%m%d%H%M%S%f')
            cursor=conn.execute('INSERT INTO loans(code,reader_id,employee_id,borrow_date,due_date) VALUES(?,?,?,?,?)',(code,reader_id,session['employee_id'],date.today().isoformat(),d['due_date']))
            conn.execute('INSERT INTO loan_items(loan_id,book_id,quantity) VALUES(?,?,?)',(cursor.lastrowid,book_id,qty))
        return success(message='Đã lập phiếu mượn.')
    except (ValueError,sqlite3.IntegrityError):return fail('Thông tin phiếu mượn không hợp lệ.')

@app.post('/api/loans/<int:id>/return')
@employee_only
def api_return_loan(id):
    with db() as conn:
        loan=conn.execute('SELECT status FROM loans WHERE id=?',(id,)).fetchone()
        if not loan or loan['status']!='Đang mượn':return fail('Phiếu không ở trạng thái đang mượn.')
        for x in conn.execute('SELECT book_id,quantity FROM loan_items WHERE loan_id=?',(id,)):
            conn.execute('UPDATE books SET available=available+? WHERE id=?',(x['quantity'],x['book_id']))
        conn.execute("UPDATE loans SET status='Đã trả',return_date=? WHERE id=?",(date.today().isoformat(),id))
    return success(message='Đã nhận sách trả.')

@app.post('/api/loans/<int:id>/renew')
@employee_only
def api_renew_loan(id):
    with db() as conn:
        loan=conn.execute('SELECT status,due_date FROM loans WHERE id=?',(id,)).fetchone()
        if not loan or loan['status']!='Đang mượn' or loan['due_date']<date.today().isoformat():return fail('Phiếu không thể gia hạn.')
        due=(date.fromisoformat(loan['due_date'])+timedelta(days=7)).isoformat()
        conn.execute('UPDATE loans SET due_date=? WHERE id=?',(due,id))
    return success(message='Đã gia hạn thêm 7 ngày.')

@app.get('/api/reservations')
@employee_only
def api_reservations():return success(items=rows('SELECT r.*,b.title,d.name reader,b.available FROM reservations r JOIN books b ON b.id=r.book_id JOIN readers d ON d.id=r.reader_id ORDER BY r.id DESC'))

@app.post('/api/reservations/<int:id>/status')
@employee_only
def api_reservation_status(id):
    d=body();status=d.get('status')
    if status not in ('Đã thông báo','Đã hủy','Hoàn tất'):return fail('Trạng thái không hợp lệ.')
    with db() as conn:
        row=conn.execute('SELECT r.status,b.available FROM reservations r JOIN books b ON b.id=r.book_id WHERE r.id=?',(id,)).fetchone()
        if not row:return fail('Không tìm thấy yêu cầu.',404)
        if status=='Hoàn tất' and row['status']!='Đã thông báo':return fail('Cần thông báo trước khi hoàn tất.')
        if status=='Đã thông báo' and row['available']<1:return fail('Sách chưa có sẵn.')
        if row['status'] in ('Hoàn tất','Đã hủy'):return fail('Yêu cầu đã xử lý.')
        conn.execute('UPDATE reservations SET status=? WHERE id=?',(status,id))
    return success(message='Đã cập nhật đặt trước.')

@app.get('/api/alerts')
@employee_only
def api_alerts():
    return success(items=rows("""SELECT l.*,r.name reader,r.email,r.phone FROM loans l JOIN readers r ON r.id=l.reader_id WHERE l.status='Đang mượn' AND l.due_date<=? ORDER BY l.due_date""",((date.today()+timedelta(days=3)).isoformat(),)))

@app.post('/api/alerts/<int:id>/mark')
@employee_only
def api_mark_reminder(id):
    with db() as conn:
        loan=conn.execute("SELECT status FROM loans WHERE id=?",(id,)).fetchone()
        if not loan or loan['status']!='Đang mượn':return fail('Phiếu không còn đang mượn.')
        conn.execute('INSERT INTO reminders(loan_id,employee_id,reminder_date,note) VALUES(?,?,?,?)',(id,session['employee_id'],datetime.now().isoformat(timespec='seconds'),body().get('note','')[:300]))
    return success(message='Đã ghi nhận nhắc hạn (không gửi SMS/email tự động).')

@app.get('/api/reports')
@employee_only
def api_reports():
    return success(categories=rows("SELECT COALESCE(c.name,'Chưa phân loại') name,SUM(b.quantity) total FROM books b LEFT JOIN categories c ON c.id=b.category_id GROUP BY b.category_id ORDER BY total DESC"),
        monthly=rows('SELECT substr(borrow_date,1,7) month,COUNT(*) total FROM loans GROUP BY month ORDER BY month DESC LIMIT 12'),
        popular=rows('SELECT b.title,SUM(li.quantity) total FROM loan_items li JOIN books b ON b.id=li.book_id GROUP BY b.id ORDER BY total DESC LIMIT 10'))

@app.get('/api/activity')
@employee_only
def api_activity():return success(items=rows('SELECT a.*,e.name employee FROM audit_logs a LEFT JOIN employees e ON e.id=a.employee_id ORDER BY a.id DESC LIMIT 100'))

@app.get('/api/reader/home')
@reader_only
def api_reader_home():
    rid=session['reader_id']
    return success(books=rows('SELECT b.*,c.name category FROM books b LEFT JOIN categories c ON c.id=b.category_id ORDER BY b.title'),
      reservations=rows('SELECT r.*,b.title FROM reservations r JOIN books b ON b.id=r.book_id WHERE r.reader_id=? ORDER BY r.id DESC',(rid,)),
      loans=rows("SELECT l.*,GROUP_CONCAT(b.title,', ') titles FROM loans l JOIN loan_items li ON li.loan_id=l.id JOIN books b ON b.id=li.book_id WHERE l.reader_id=? GROUP BY l.id ORDER BY l.id DESC",(rid,)))

@app.post('/api/reader/reserve/<int:book_id>')
@reader_only
def api_reader_reserve(book_id):
    with db() as conn:
        book=conn.execute('SELECT id FROM books WHERE id=?',(book_id,)).fetchone()
        if not book:return fail('Không tìm thấy sách.',404)
        duplicate=conn.execute("SELECT id FROM reservations WHERE reader_id=? AND book_id=? AND status='Chờ xử lý'",(session['reader_id'],book_id)).fetchone()
        if duplicate:return fail('Bạn đã đặt trước sách này.')
        conn.execute('INSERT INTO reservations(reader_id,book_id,reserved_at) VALUES(?,?,?)',(session['reader_id'],book_id,datetime.now().isoformat(timespec='seconds')))
    return success(message='Đã gửi yêu cầu đặt sách.')
