# Smart Library – Hệ thống quản lý thư viện Flask

## Cài đặt
```bash
cd library_modern
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Mở http://127.0.0.1:5001. Tài khoản demo: `admin` / `admin`.

## Chức năng mới
1. **Tra cứu nâng cao**: lọc theo tên/mã/tác giả/NXB, thể loại và số lượng còn.
2. **Đặt trước sách**: thủ thư ghi nhận yêu cầu, tránh trùng đặt trước, thông báo thủ công khi có sách.
3. **Gia hạn mượn**: cộng thêm 7 ngày cho phiếu chưa quá hạn.
4. **Trung tâm cảnh báo**: các phiếu quá hạn hoặc đến hạn trong 3 ngày tới, yêu cầu đặt trước đã có sách.
5. **Lịch sử mượn trả**: tìm theo mã phiếu/mã hoặc tên độc giả.
6. **Xuất CSV**: danh mục sách, độc giả, phiếu mượn (UTF-8 hỗ trợ Excel).
7. **Sửa thông tin sách và độc giả**: không làm sai lệch số sách đang mượn.
8. **Nhật ký thao tác**: ghi hoạt động của một số tính năng mới.

## Chú ý
- Dự án vẫn sử dụng SQLite. Dữ liệu trong `library.db` đang có sẽ được giữ nguyên khi chạy bản này trong cùng thư mục có database cũ (nên sao lưu trước).
- Bản mẫu chưa phù hợp triển khai Internet: cần đổi mật khẩu mặc định, hash mật khẩu, khóa bí mật từ biến môi trường, tắt debug, thêm CSRF protection và kiểm tra phân quyền sâu hơn.
- Chức năng đặt trước mới chỉ quản lý yêu cầu nội bộ, **không gửi email/SMS**, không giữ chỗ tự động.
- Gia hạn hiện chưa giới hạn số lần; nên thêm quy định nghiệp vụ nếu dùng thực tế.
