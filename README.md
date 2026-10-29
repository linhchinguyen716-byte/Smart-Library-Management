# Smart Library — Hệ thống Quản lý Thư viện Thông minh
---

## 1. Kiến trúc thư mục (Repository Architecture)

```text
Smart-Library-Management/
├── backend/
│   ├── api/
│   │   ├── analytics.py
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── circulation.py
│   │   ├── common.py
│   │   ├── people.py
│   │   └── reader_portal.py
│   ├── routes/
│   │   ├── alerts.py
│   │   ├── api.py
│   │   ├── auth.py
│   │   ├── catalog.py
│   │   ├── dashboard.py
│   │   ├── loans.py
│   │   ├── people.py
│   │   ├── reports.py
│   │   └── reservations.py
│   ├── app.py
│   ├── config.py
│   ├── core.py
│   ├── database.py
│   └── middleware.py
├── frontend/
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── admin/
│       ├── auth/
│       ├── layouts/
│       └── reader/
├── react-frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── style.css
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── .env.example
├── .gitignore
├── library.db
├── library-backup.db
├── README.md
├── requirements.txt
└── run.py
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

- **Trang chủ Tra cứu cộng đồng:** `http://127.0.0.1:5001/` (Khách và độc giả xem & tìm kiếm sách trực tiếp không cần đăng nhập).
- **Cổng Độc giả:**
  - Đăng nhập: `http://127.0.0.1:5001/user/login`
  - Đăng ký thẻ: `http://127.0.0.1:5001/user/register`
  - Không gian cá nhân: `http://127.0.0.1:5001/user`
- **Cổng Quản trị viên / Thủ thư:**
  - Đăng nhập quản trị: `http://127.0.0.1:5001/admin/login` (hoặc `/login`)
  - Bảng điều khiển trung tâm: `http://127.0.0.1:5001/dashboard` (hoặc `/admin`)
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

- **Bí mật & Môi trường:** Sao chép file `.env.example` thành `.env` và đặt biến môi trường `SECRET_KEY` bằng khóa ngẫu nhiên dài trước khi đưa lên môi trường mạng.
- **Mạng cục bộ (LAN) & Camera:** Khi dùng camera quét mã QR qua điện thoại/máy tính bảng trong mạng LAN, trình duyệt yêu cầu kết nối an toàn qua giao thức **HTTPS**.
- **Bản sao lưu:** Luôn tạo bản sao lưu định kỳ cho file `library.db` trước khi thực hiện nâng cấp schema hoặc di chuyển dữ liệu.
