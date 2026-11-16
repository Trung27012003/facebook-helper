**Facebook Helper 0.4.2 — Windows 10/11 64-bit**

Tải ZIP, giải nén toàn bộ, chạy `FacebookHelper/FacebookHelper.exe`. Đóng bản cũ trước khi mở; giữ nguyên `_internal`. Bài, nhóm, ảnh và lịch sử cũ được giữ.

Luồng đăng mới:

1. **Tự đăng bài** được bật sẵn. Chọn bài/nhóm, bấm **Bắt đầu tự đăng** và xác nhận.
2. Ứng dụng dán HTML, đính kèm ảnh, chờ ảnh tải xong và nút Đăng sẵn sàng, rồi bấm **Đăng**.
3. Sau gửi, xác nhận kết quả để tiếp tục nhóm sau. Chế độ tự đăng được giữ, không bị chuyển ngầm về chỉ chuẩn bị.

**Bỏ hẳn lỗi chặn “bản lưu 374 / Facebook 788”**: không còn so số ký tự, độ dài hay so khớp nội dung/định dạng đọc lại với bản lưu. Đây từng là điều kiện của ứng dụng, không phải giới hạn bài viết của Facebook. Chỉ kiểm tra chữ đã xuất hiện và trạng thái tải ảnh/nút bấm. Định dạng cuối cùng phụ thuộc Facebook và cần được người dùng kiểm tra.

**Đăng bản đang mở**: nếu bản nháp Facebook đã có đủ chữ/ảnh, kiểm tra rồi chọn nút này để ứng dụng bấm Đăng, không dán thêm hoặc thêm lại ảnh. Kiểm tra đúng nhóm và xác nhận trước khi gửi.

Bỏ chọn **Tự đăng bài** nếu chỉ muốn điền bài rồi tự bấm Đăng. Tiến trình hiển thị rõ các bước mở nhóm, dán, thêm ảnh, chờ nút và gửi.

Vẫn dừng khi ô trống, ảnh chưa tải xong/thiếu tệp, sai nhóm, Facebook báo lỗi/hạn chế/xác thực hoặc kết quả gửi chưa rõ. Không tự bấm lại khi chưa rõ kết quả. Không có cam kết tránh kiểm duyệt hay xóa bài.

125 test tự động đạt, có bài dài hơn 15.000 ký tự kèm nhiều ảnh, DOM đọc lại khác nguồn, chờ upload và đăng bản đang mở. Luồng Facebook kiểm tra bằng mô phỏng, chưa xác nhận trực tiếp trên tài khoản người dùng. Gói `.exe` được kiểm tra trên Windows trước phát hành.

Bản chưa ký mã số; SHA256 đi kèm để kiểm tra tính toàn vẹn.
