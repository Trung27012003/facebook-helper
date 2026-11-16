# Kiểm thử bản 0.2

Ngày: 16/11/2026 (Asia/Saigon). Môi trường Linux, Python 3.12.14, PySide6 6.12.0, Playwright 1.65.2 và Chromium. Giao diện chạy Qt offscreen, trình duyệt dùng trang HTML mô phỏng. Không đăng bài Facebook thật trong test.

Kết quả tự động: **88 test đạt**, gồm 60 ca của bản trước và 28 ca bổ sung. Log: [test-output-v0.2.txt](test-output-v0.2.txt).

| Phần mới | Các kiểm tra chính | Kết quả |
|---|---|---|
| Mẫu bài | Trường bắt buộc, bố cục theo mẫu tham khảo, tiêu đề/các phần/•, Unicode, ký tự HTML; tạo và hủy bằng giao diện | Đạt |
| Nhãn nhóm | Nhiều nhãn một nhóm, nhiều nhóm cùng nhãn, loại trùng/không phân biệt hoa thường, khớp chính xác | Đạt |
| Chọn nơi đăng | Chọn nhiều nhóm hoặc nhãn, tự tích đúng nhóm, bỏ bớt nhóm, tạo danh sách có thứ tự | Đạt |
| Dữ liệu | Khử nhóm trùng, giữ thứ tự, không tạo dữ liệu dở dang khi lỗi giữa chừng | Đạt |
| Nâng cấp | Dữ liệu schema 0.1 được giữ nguyên khi nâng cấp, mở lại không lỗi | Đạt |
| Danh sách có kiểm tra | Chuẩn bị lần lượt, ghi kết quả, tiếp tục bỏ qua nhóm đã xử lý | Đạt |
| Tự gửi | Bắt buộc xác nhận, gửi ba nhóm đúng thứ tự và mỗi nhóm một lần, chờ giữa nhóm | Đạt (mô phỏng) |
| Kiểm soát | Tạm dừng khi chờ/đang gửi, bỏ qua, đổi danh sách dừng lịch chuyển, chặn tạo danh sách mới khi đang chạy | Đạt |
| Tránh trùng | Sau lỗi bấm gửi không rõ kết quả hoặc tắt giữa chừng: dừng và yêu cầu kiểm tra, không tự thử lại | Đạt |
| Trình duyệt | Tìm/mở cửa sổ soạn, chế độ chuẩn bị không bấm Đăng, tự gửi chỉ sau khi điền, dừng khi không tìm được ô | Đạt (mô phỏng) |
| Trạng thái và lịch sử | Thứ tự bảng khớp thứ tự đăng; kết quả các danh sách độc lập; lỗi trước/sau bấm gửi phân biệt được | Đạt |
| Đóng gói | Qt, Chromium, bốn tab và worker khởi động/đóng sạch trong tiến trình kiểm tra | Đạt trên Linux; Windows xem workflow phát hành |

Các ca mới nằm trong `tests/test_batches.py`, `tests/test_queue_ui.py`, `tests/test_template_ui.py` và phần bổ sung của `tests/test_browser.py`. Các test 0.1 tiếp tục chạy, không thay bằng kiểm tra thủ công.

## Cần kiểm tra thực tế

- Chạy gói trên máy Windows cá nhân, kiểm tra bố cục ở độ phân giải và mức phóng to chữ thực tế.
- Đăng nhập Facebook, nhóm công khai/riêng tư và nhóm có kiểm duyệt.
- Bài theo mẫu có nhiều ảnh, kiểm tra xuống dòng và ảnh sau khi đăng.
- Chọn nhãn gồm hai nhóm thử, kiểm tra từng nhóm trước; sau đó thử tùy chọn tự gửi với bài và nhóm được phép dùng.
- Trường hợp Facebook đổi ngôn ngữ, tải ảnh chậm, mất mạng, xuất hiện xác thực hoặc hạn chế đăng.
- Thử tạm dừng, đóng giữa lúc gửi và mở lại; kiểm tra bài đã gửi trước khi cập nhật trạng thái/tiếp tục.
- Lấy permalink, chụp đúng bài, phân biệt gửi xong/chờ duyệt/đã hiển thị.

Các ca Facebook thật ở trên **chưa thực hiện** vì không có tài khoản và nhóm thử trong môi trường này. Kết quả mô phỏng không khẳng định tương thích với giao diện Facebook hiện hành.
