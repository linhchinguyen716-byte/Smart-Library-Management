# Smart Library — Hệ thống Quản trị Thư viện Thông minh

Hệ thống quản lý thư viện hiện đại với kiến trúc phân tách rõ ràng giữa **Backend (Flask + SQLite)**, **Server-Side Rendered Frontend (Jinja2 Templates)** và **Single Page Application (React 19 + Vite)**.

---

## 1. Kiến trúc thư mục (Repository Architecture)

```text
Smart-Library-Management/
├── backend/                       # Backend lõi (Flask + SQLite)
│   ├── api/                       # Phân hệ RESTful JSON API (/api/*)
│   │   ├── common.py              # Tiện ích JSON, decorators phân quyền, CSRF/Origin guard
│   │   ├── auth.py                # API phiên đăng nhập, đăng ký, đăng xuất
│   │   ├── catalog.py             # API quản lý sách & thể loại
│   │   ├── people.py              # API quản lý độc giả & nhân viên
│   │   ├── circulation.py         # API mượn, trả, gia hạn, đặt trước, cảnh báo
│   │   ├── analytics.py           # API tổng quan, báo cáo thống kê, nhật ký
│   │   └── reader_portal.py       # API không gian độc giả cá nhân
│   ├── routes/                    # Web SSR Routes (Jinja2 Rendered)
│   │   ├── auth.py                # Điều hướng đăng nhập Admin & Độc giả
│   │   ├── dashboard.py           # Bảng điều khiển tổng quan
│   │   ├── catalog.py             # Quản lý kho sách, thể loại, QR Code, máy quét
│   │   ├── people.py              # Quản lý hồ sơ độc giả & nhân sự
│   │   ├── loans.py               # Quản lý mượn/trả, gia hạn, lịch sử, quá hạn
│   │   ├── reservations.py        # Quản lý hàng chờ đặt trước
│   │   ├── alerts.py              # Cảnh báo hạn trả & nhắc nhở
│   │   ├── reports.py             # Thống kê, xuất CSV, nhật ký kiểm toán
│   │   └── api.py                 # Module liên kết API phục vụ SPA
│   ├── config.py                  # Cấu hình đường dẫn, biến môi trường, bí mật
│   ├── database.py                # Quản lý kết nối SQLite & khởi tạo bảng / seed data
│   ├── middleware.py              # Phân quyền (login_required, reader_required) & audit logs
│   ├── core.py                    # Khởi tạo Flask App & cấu hình nạp template đa thư mục
│   └── app.py                     # Entrypoint module của backend
│
├── frontend/                      # Giao diện Server-Side Rendering (Flask Jinja2)
│   ├── static/                    # Tệp tĩnh (CSS hệ thống, phong cách biên tập)
│   │   └── style.css
│   └── templates/                 # Giao diện HTML Jinja2 phân nhóm theo vai trò
│       ├── layouts/               # Khung bố cục (base.html, user_base.html)
│       ├── auth/                  # Màn hình xác thực (login, user_login, user_register)
│       ├── admin/                 # 18 màn hình quản trị dành cho thủ thư/admin
│       └── reader/                # Màn hình không gian cá nhân của độc giả (user_home)
│
├── react-frontend/                # Giao diện Single Page Application (React 19 + Vite)
│   ├── src/
│   │   ├── services/api.js        # HTTP client kết nối trực tiếp đến backend /api
│   │   ├── hooks/useData.js       # Custom hook lấy và đồng bộ dữ liệu
│   │   ├── components/ui/         # Các thành phần giao diện dùng chung (Header, Panel, Table, Modal...)
│   │   ├── pages/                 # Các trang nghiệp vụ React độc lập
│   │   ├── App.jsx                # Shell ứng dụng và điều hướng
│   │   ├── main.jsx               # Điểm gắn kết DOM
│   │   └── style.css              # Giao diện React SPA
│   ├── package.json
│   └── vite.config.js             # Cấu hình Vite Dev Server & Reverse Proxy (/api -> :5001)
│
├── library.db                     # Cơ sở dữ liệu SQLite chính
├── library-backup.db              # Bản sao lưu an toàn của cơ sở dữ liệu
├── requirements.txt               # Danh sách thư viện Python
├── run.py                         # File khởi động chính của ứng dụng
└── README.md                      # Tài liệu hướng dẫn dự án
```

---

## 2. Hướng dẫn cài đặt & Khởi chạy

### Bước 1: Môi trường Backend (Flask)

```powershell
# Tạo và kích hoạt môi trường ảo Python
python -m venv venv
.\venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Khởi chạy máy chủ Backend
python run.py
```
> **Cổng mặc định:** `http://127.0.0.1:5001`

### Bước 2: Môi trường Frontend SPA (React + Vite) — *Tùy chọn*

Nếu muốn sử dụng giao diện React SPA hiện đại song song với giao diện Jinja2:

```bash
cd react-frontend
npm install
npm run dev
```
> **Địa chỉ React:** `http://127.0.0.1:5173` (Vite tự động proxy các yêu cầu `/api/*` về backend cổng `5001`).

---

## 3. Các cổng truy cập (Web Portals)

- **Cổng Quản trị viên / Thủ thư:** `http://127.0.0.1:5001/admin/login` (hoặc `/login`)
- **Cổng Độc giả Đăng nhập:** `http://127.0.0.1:5001/user/login`
- **Cổng Độc giả Đăng ký:** `http://127.0.0.1:5001/user/register`
- **Giao diện React SPA:** `http://127.0.0.1:5173`

### Tài khoản quản trị & Bảo mật
- **Database hiện tại:** Tài khoản quản trị có sẵn là `admin`, mật khẩu tự động băm an toàn (`pbkdf2:sha256` / `scrypt`) ngay trong lần đăng nhập đầu tiên.
- **Khởi tạo database mới:** Đặt biến môi trường `INITIAL_ADMIN_PASSWORD` trước khi chạy (ví dụ trên PowerShell: `$env:INITIAL_ADMIN_PASSWORD='MatKhauManhCuaBan2026!'`).

---

## 4. Danh sách tính năng cốt lõi

1. **Tra cứu & Tìm kiếm nâng cao:** Lọc theo mã sách, nhan đề, tác giả, nhà xuất bản, chuyên mục và tình trạng còn sách trong kho.
2. **Định danh QR Code & Máy quét:** Tạo động mã QR cho từng đầu sách, in nhãn dán lưu trữ và tích hợp Web BarcodeDetector quét qua camera / máy quét mã vạch USB.
3. **Quản lý Mượn / Trả & Gia hạn:** Lập phiếu mượn nhiều bản, trừ tồn kho tức thời, thu hồi sách hoàn kho và gia hạn thêm 7 ngày.
4. **Hàng chờ Đặt trước (Reservations):** Tiếp nhận đặt chỗ khi sách tạm hết, theo dõi trạng thái `Chờ xử lý` → `Đã thông báo` → `Hoàn tất`.
5. **Trung tâm Cảnh báo & Nhắc hạn:** Tự động lọc các phiếu quá hạn hoặc cận hạn trong 3 ngày, hỗ trợ soạn thảo email trực tiếp và ghi sổ lịch sử nhắc nhở.
6. **Báo cáo & Phân tích trực quan:** Biểu đồ cơ cấu thể loại, biểu đồ tăng trưởng mượn sách theo tháng và Top 10 ấn phẩm lưu thông cao nhất.
7. **Xuất dữ liệu chuẩn CSV:** Xuất danh mục Sách, Độc giả, Phiếu mượn với định dạng UTF-8 BOM hiển thị chuẩn trên Microsoft Excel.
8. **Nhật ký kiểm toán (Audit Trail):** Ghi nhận vết mọi thao tác thay đổi dữ liệu quan trọng phục vụ đối soát.

---

## 5. Lưu ý khi triển khai thực tế (Production Readiness)

- **Bí mật & Môi trường:** Đặt biến môi trường `SECRET_KEY` bằng khóa ngẫu nhiên dài trước khi đưa lên môi trường mạng.
- **Mạng cục bộ (LAN) & Camera:** Khi dùng camera quét mã QR qua điện thoại/máy tính bảng trong mạng LAN, trình duyệt yêu cầu kết nối an toàn qua giao thức **HTTPS**.
- **Bảo sao lưu:** Luôn tạo bản sao lưu định kỳ cho file `library.db` trước khi thực hiện nâng cấp schema hoặc di chuyển dữ liệu.
