Bản **0.4.0** cho Windows 10/11 64-bit. Tải ZIP, giải nén toàn bộ rồi chạy `FacebookHelper/FacebookHelper.exe`. Giữ nguyên `_internal`; dữ liệu cũ được giữ.

Sửa đúng phần soạn thảo:

- Thay thanh nút tự ghép bằng **Summernote 0.9.1 nguyên bản**, đóng kèm offline trong Qt WebEngine; có đầy đủ toolbar thư viện.
- Dán từ Facebook tự bỏ nền tối/màu giao diện, giữ chữ đậm/nghiêng, tiêu đề và danh sách. Sửa khi mở các bản nháp Qt cũ bị nền tối.
- Lưu cả HTML trong lượt đăng mới. Dán sang Facebook qua clipboard **text/html**, chuyển kiểu chữ đậm/nghiêng từ CSS sang HTML ngữ nghĩa.
- Kiểm tra nội dung và các định dạng chính sau dán. Nếu Facebook loại bỏ định dạng, dừng trước khi Đăng; không tự đăng bản mất định dạng.

Thay đổi cách gửi để kiểm tra kết quả:

- **Dừng sau mỗi lần bấm Đăng**; cần xác nhận bài còn hiển thị hoặc chờ duyệt trước khi tiếp tục.
- Khi thấy cảnh báo hạn chế, yêu cầu xác thực hoặc thông báo xóa/gỡ: dừng và giữ thông báo. Không tự gửi lại khi kết quả chưa rõ.
- Không có tính năng né phát hiện, vượt xác thực hoặc bảo đảm bài không bị Facebook/quản trị viên xóa. Không thể xác định nguyên nhân chỉ từ việc bài biến mất.

Giới hạn: Facebook hỗ trợ một phần định dạng, không toàn bộ font/màu như Word. Clipboard không có HTML thì không phục hồi được kiểu chữ. Thêm ảnh bằng nút Thêm ảnh. Các lượt lịch sử cũ chỉ có chữ thuần không tự khôi phục HTML; tạo danh sách mới từ bài đã lưu nếu cần dán định dạng.

Gói được kiểm tra khởi động Summernote, clipboard và Chromium trên Windows. Test luồng đăng dùng mô phỏng, chưa xác nhận trực tiếp trên tài khoản Facebook của người dùng. Kiểm tra cảnh báo không phát hiện được mọi trường hợp bài bị gỡ âm thầm.

Bản chưa ký mã số; SHA256 nằm trong `SHA256SUMS.txt`. Thư viện và giấy phép kèm trong gói.
