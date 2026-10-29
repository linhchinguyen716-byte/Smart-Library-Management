# Smart Library — React Single Page Application (SPA)

Phân hệ giao diện Single Page Application (SPA) hiện đại được xây dựng bằng **React 19** và **Vite**, hoạt động song song hoặc độc lập cùng Backend Flask thông qua giao tiếp RESTful JSON API.

---

## 1. Yêu cầu môi trường

- **Node.js:** Phiên bản 18+ (khuyên dùng Node.js 20 LTS trở lên).
- **Trình quản lý gói:** `npm`, `yarn`, hoặc `pnpm`.

---

## 2. Cài đặt & Khởi chạy

### Cài đặt dependencies:
```bash
npm install
```

### Chạy môi trường phát triển (Dev Server):
```bash
npm run dev
```
- Ứng dụng chạy tại địa chỉ: `http://127.0.0.1:5173/`
- Vite đã được cấu hình Reverse Proxy tự động chuyển tiếp toàn bộ yêu cầu bắt đầu bằng `/api/*` về máy chủ Flask (`http://127.0.0.1:5001/api/*`), không gặp rào cản CORS.

### Đóng gói cho Production (Build):
```bash
npm run build
```
- Kết quả biên dịch tối ưu sẽ được lưu tại thư mục `dist/`.

### Xem trước bản build (Preview):
```bash
npm run preview
```

---

## 3. Cấu trúc thư mục mã nguồn (`src/`)

```text
src/
├── services/
│   └── api.js              # HTTP client fetch, tự động quản lý credentials và parse JSON lỗi
├── hooks/
│   └── useData.js          # Custom React hook dùng để fetch và refetch dữ liệu linh hoạt
├── components/
│   └── ui/
│       └── Common.jsx      # Bộ UI components: Modal, MetricCard, Table, ActionButtons, Form fields
├── pages/
│   ├── AuthPage.jsx        # Đăng nhập & Đăng ký (hỗ trợ chuyển đổi tab giữa Admin và Độc giả)
│   ├── DashboardPage.jsx   # Tổng quan số liệu thống kê & biểu đồ
│   ├── BooksPage.jsx       # Quản lý kho sách, tiếp nhận và chỉnh sửa ấn phẩm
│   ├── LoansPage.jsx       # Quản lý mượn/trả, gia hạn hạn trả
│   ├── ReaderHomePage.jsx  # Không gian độc giả: xem sách, đặt trước, theo dõi mượn
│   ├── ReservationsPage.jsx# Danh sách hàng chờ đặt trước & thông báo có sách
│   ├── AlertsPage.jsx      # Cảnh báo trễ hạn & nhắc hạn trả
│   ├── ReportsPage.jsx     # Báo cáo thống kê trực quan & xuất CSV
│   ├── ActivityPage.jsx    # Nhật ký kiểm toán thao tác hệ thống
│   └── GenericCrudPage.jsx # Quản lý Độc giả, Thể loại, Nhân sự
├── App.jsx                 # App shell, sidebar điều hướng, quản lý phiên đăng nhập
├── main.jsx                # Entrypoint gắn React vào root DOM
└── style.css               # Hệ thống styling với Design System chuẩn hóa
```

---

## 4. Tích hợp Backend

Khi chạy song song:
1. Đảm bảo Backend Flask đang chạy tại cổng `5001` (`python run.py`).
2. Chạy React Vite Dev Server tại cổng `5173` (`npm run dev`).
3. Truy cập `http://127.0.0.1:5173` để trải nghiệm SPA hoàn chỉnh với state quản lý linh hoạt và chuyển trang không tải lại (Client-side routing).
