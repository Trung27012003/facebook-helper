# Kiểm thử 0.4: Summernote, định dạng và xác nhận kết quả đăng

Ngày 16/11/2026 (Asia/Saigon). Linux, Python 3.12.14, PySide6 6.12.0, Chromium Playwright. **109 test đạt (42.64 giây)**. Kết quả lệnh đầy đủ ở [test-output-v0.4.txt](test-output-v0.4.txt).

Các ca chính:

- Thực sự tải Summernote **0.9.1** và toolbar nguyên bản trong Qt WebEngine, sử dụng tài nguyên local.
- Dán mẫu Facebook với nền #242526/chữ sáng: bỏ nền/màu giao diện, giữ b/i/ul/li; sửa bản nháp qrichtext cũ.
- Định dạng Word, highlight chủ ý, bảng, clipboard HTML/text, hashtag và lưu/mở lại.
- Lượt đăng mới lưu snapshot HTML, không chỉ plain text; sửa bài gốc không đổi lịch sử.
- Chromium nhận HTML qua Clipboard API và Ctrl+V: ô soạn giữ chữ đậm và danh sách.
- Ô soạn mô phỏng chỉ nhận chữ thuần: dừng trước nút Đăng, không fallback âm thầm.
- Cảnh báo hạn chế trước điền: không sửa ô; thông báo bài bị gỡ sau bấm: dừng, ghi kết quả chưa rõ.
- Sau mỗi lần gửi: không tự chuyển nhóm; kết quả chưa xác nhận chặn gửi lại/tiếp tục.
- Các kiểm tra dữ liệu, chọn nhãn/nhiều nhóm, export và sao lưu của bản trước tiếp tục chạy.

Đã kiểm tra wheel chứa editor HTML/JS, jQuery, Summernote JS/CSS, DOMPurify và font icon. Ảnh giao diện thật: [Summernote](images/editor-v0.4.png).

Chưa có tài khoản/nhóm Facebook thật trong môi trường để xác minh giao diện hiện hành hoặc nguyên nhân bài người dùng bị xóa. Mô phỏng không chứng minh bài sẽ được Facebook giữ lại. Việc dừng khi thấy cảnh báo không phát hiện mọi hình thức gỡ bài âm thầm; vì vậy cần kiểm tra trực tiếp sau mỗi bài.

Không có thay đổi che giấu browser automation, giả fingerprint, xoay IP/tài khoản hoặc vượt xác thực. Các cờ tắt sandbox/GPU trong môi trường test Linux chỉ phục vụ Qt WebEngine chạy trong container; không được đưa vào cấu hình trình duyệt Facebook của sản phẩm.

Bổ sung: kiểm tra lệnh font/màu thực tế của Summernote, chặn lịch sử chỉ có chữ thuần, và chống callback cũ đánh dấu nhầm bài vừa lưu/chuyển bài. Kết quả lưu dùng revision và generation để bỏ qua thông báo editor về muộn. Workflow phát hành yêu cầu CI mã nguồn thành công trước khi công khai ZIP.
