# Smart Library - bản tách thư mục + 2 đăng nhập

## Chạy trên Windows trong VS Code

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

- Admin / Nhân viên: http://127.0.0.1:5001/admin/login
- Độc giả: http://127.0.0.1:5001/user/login
- Đăng ký độc giả: http://127.0.0.1:5001/user/register

### Tài khoản quản trị

Nếu bạn đã có `library.db`, tài khoản quản trị cũ vẫn giữ nguyên, và mật khẩu cũ được tự động băm khi đăng nhập thành công. Nếu tạo database mới, ứng dụng không còn dùng mật khẩu admin/admin cố định. Hãy đặt biến môi trường `INITIAL_ADMIN_PASSWORD` trước lần khởi động đầu tiên, ví dụ PowerShell: `$env:INITIAL_ADMIN_PASSWORD='MatKhauManhCuaBan2026!'`.

## Cấu trúc

- `backend/app.py`: Flask, SQLite, các route xử lý.
- `frontend/templates`: HTML/Jinja2.
- `frontend/static`: CSS.
- `run.py`: khởi động ứng dụng.

Đây là tách code theo thư mục, frontend vẫn được Flask render (chưa phải frontend SPA/REST API độc lập).

Tài khoản độc giả đăng ký mới tạo một hồ sơ readers mới. Muốn liên kết các độc giả cũ, cần tính năng cấp tài khoản/xác minh của quản trị viên. Cần CSRF protection, rate limiting và kiểm thử bảo mật trước khi triển khai Internet. Sao lưu `library.db` trước khi nâng cấp.
