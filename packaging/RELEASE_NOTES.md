**Facebook Helper 0.4.1 — Windows 10/11 64-bit**

Tải ZIP, giải nén toàn bộ rồi mở `FacebookHelper/FacebookHelper.exe`. Giữ nguyên `_internal`; không cần cài Python. Bài, ảnh, nhóm, nhãn và lịch sử cũ được giữ.

Sửa lỗi dừng với thông báo “Nội dung trong ô Facebook khác bài đã lưu sau khi dán” dù nhìn thấy đủ chữ:

- Đối chiếu Unicode tiếng Việt tương đương và marker danh sách trên cả hai phía.
- Chờ Facebook cập nhật xong; đọc lại DOM/Range, bỏ phần điều khiển không thuộc nội dung bài.
- Dán chữ trước, đính kèm ảnh sau; kiểm tra lại nếu Facebook tạo lại ô soạn.
- Vẫn chặn thiếu đoạn hoặc sai số tiền. Không bỏ kiểm tra nội dung, không dán lại gây trùng.
- Bài đã chuẩn bị có hướng dẫn bước tiếp; hiển thị phiên bản ở tiêu đề ứng dụng.

**Chế độ mặc định:** bạn tự kiểm tra và bấm **Đăng** trong Facebook. Chỉ chuẩn bị bài không đồng nghĩa đã gửi. Nếu đã có một bản nháp đủ chữ/ảnh trong Facebook, bạn có thể kiểm tra và đăng thủ công rồi cập nhật kết quả; không bấm Bắt đầu nhiều lần để dán chồng.

Summernote nguyên bản và dán HTML tiếp tục được giữ. Sau mỗi bài vẫn cần xác nhận kết quả trước khi chuyển nhóm; không có bảo đảm tránh Facebook kiểm duyệt/xóa bài.

116 test tự động đạt; gói `.exe` được kiểm tra trên Windows trước phát hành. Kiểm thử luồng Facebook dùng mô phỏng, chưa xác minh trên tài khoản thật của người dùng. Nguồn sai khác cụ thể ở máy người dùng chưa được xác định chỉ từ ảnh.

Bản chưa ký mã số. File SHA256 đi kèm để đối chiếu tính toàn vẹn.
