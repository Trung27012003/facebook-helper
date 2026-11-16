# Kiểm thử 0.4.2: luồng tự đăng theo trạng thái sẵn sàng

Ngày 16/11/2026 (Asia/Saigon). **125/125 test đạt**, 69.15 giây. Log: [test-output-v0.4.2.txt](test-output-v0.4.2.txt).

Thay đổi theo yêu cầu người dùng: loại bỏ kiểm tra so khớp số ký tự, văn bản chuẩn hóa và định dạng DOM. Chỉ chờ chữ được nhận, trạng thái tải ảnh và nút Đăng sẵn sàng. Các test về chặn thiếu đoạn/sai số tiền bằng đối chiếu của bản trước được thay bằng kiểm tra hành vi mới, không còn là cam kết của sản phẩm.

| Ca | Kết quả |
|---|---|
| Bài dài 240 dòng, trên 15.000 ký tự, nhiều ảnh | Dán một lần, đợi upload xong, tự bấm Đăng |
| Phần Facebook đọc lại có thêm chữ giao diện / khác plain text nguồn | Không chặn bằng đối chiếu |
| Facebook đổi kiểu định dạng sau dán | Không chặn bằng kiểm tra kiểu chữ |
| Clipboard không đưa được chữ vào ô | Dừng, không tự dán lại / không gửi bài trống |
| Upload còn chạy hoặc hết hạn chờ | Chờ / dừng; không bấm Đăng sớm |
| Thanh progress đã 100% nhưng còn hiển thị | Không chặn vô hạn |
| Tự đăng mặc định | Checkbox bật, nút ghi Bắt đầu tự đăng; chỉ chuẩn bị khi người dùng tắt |
| Xác nhận kết quả bài trước | Nhóm sau vẫn dùng publish khi đang chọn tự đăng |
| Đăng bản đang mở | Không dán/đính kèm lại, chỉ gửi bản hiện tại sau xác nhận |
| Đăng bản đang mở khác nhóm | Chặn trước nút Đăng |
| Facebook báo hạn chế / bài bị gỡ | Dừng và giữ thông báo; không retry tự động |
| Kết quả sau click chưa rõ | Giữ uncertain, không tự gửi lại |

Các test liên quan nằm trong `tests/test_browser.py` và `tests/test_queue_ui.py`. Summernote, SQLite, nhãn nhóm, dữ liệu và sao lưu tiếp tục được kiểm tra.

Kiểm thử Facebook chạy Chromium với HTML mô phỏng, không đăng trên tài khoản thật. Bộ kiểm tra readiness không khẳng định nội dung cuối cùng giống bản lưu; cần xem lại trên Facebook. Không có bảo đảm bài không bị kiểm duyệt/gỡ.
