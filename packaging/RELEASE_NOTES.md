**Facebook Helper 0.10.0 — Setup, lịch dễ chọn và thử lại có kiểm soát**

- Có bộ cài Setup cho Windows 10/11 x64, cài theo người dùng, tạo lối tắt và gỡ cài đặt; dữ liệu/phiên Facebook ở riêng và được giữ.
- Lỗi tạm thời trước gửi được thử tối đa 3 lần. Nếu bản soạn đã sẵn sàng, dùng chính bản đang mở. Sau bấm Đăng, chỉ thử lại khi phản hồi đúng thao tác xác nhận lỗi tạm thời/chưa tạo bài. Không thử lại mù khi chưa rõ kết quả, gặp xác thực hoặc hạn chế.
- Ô ngày chuyển sang lịch tiếng Việt của Qt, bấm cả ô để chọn; hiển thị đủ ngày và có Hôm nay.
- Playwright khởi động khi cần. Gói bỏ Chromium headless dư và các tài nguyên phát triển/locale không dùng; Setup nén LZMA2. Giữ Qt WebEngine, Chromium đầy đủ và tài nguyên tiếng Việt/Anh.
- Có kiểm tra cập nhật công khai, hỏi Tải bộ cài/Để sau và kiểm tra thủ công. Thông báo hoãn khi đang đăng. Không tự cài.

Máy dùng bản cũ cần cài bản này một lần; các bản sau mới nhận thông báo trong ứng dụng. Đóng bản đang chạy trước khi cài. Không cần Python hoặc quyền quản trị.

Kiểm thử Facebook dùng mô phỏng; chưa chứng minh lỗi trên tài khoản người dùng đã hết. Bài chờ duyệt có thể chưa có link dùng được. Checksum cho Setup và ZIP đi kèm.
