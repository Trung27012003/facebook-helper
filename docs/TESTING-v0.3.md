# Kiểm thử trình soạn thảo 0.3

Ngày 16/11/2026 (Asia/Saigon). Kết quả: **105 passed** (35.61 giây): 88 ca của bản 0.2 và 17 ca rich text bổ sung. Linux, Python 3.12.14, PySide6 6.12.0; clipboard Qt offscreen và Chromium mô phỏng. Log: [test-output-v0.3.txt](test-output-v0.3.txt).

| Phần | Kiểm tra | Kết quả |
|---|---|---|
| Dán Word | HTML có class/inline CSS; font, cỡ, đậm, gạch chân, màu chữ và nền, Unicode | Đạt |
| Lưu bài | Dán định dạng, lưu, mở lại giữ kiểu chữ và danh sách | Đạt |
| Copy bài | Clipboard có HTML/chữ thuần, giữ định dạng và hashtag trong body | Đạt |
| Dán chữ thuần | Nút dán và Ctrl+Shift+V không đưa kiểu chữ nguồn vào | Đạt |
| Ctrl+V | Phím tắt nhập được định dạng HTML từ clipboard | Đạt |
| Thanh công cụ | Thay vị trí con trỏ cập nhật nút/font/cỡ; không tự sửa nội dung | Đạt |
| Danh sách | Bullet, đánh số, số bắt đầu khác 1; marker còn trong chữ xuất Facebook | Đạt |
| Tiêu đề/căn lề | Đổi heading, căn giữa, xóa định dạng giữ nội dung | Đạt |
| Bảng/link | HTML bảng/link được giữ; bảng xuất thành hàng `A | B`; chèn bảng đặt con trỏ đúng ô | Đạt |
| Hoàn tác | Undo/redo định dạng danh sách không mất chữ | Đạt |
| HTML nguồn | Không nhập script hoặc ảnh từ URL/đường dẫn; thông báo dùng Thêm ảnh | Đạt |
| Liên kết | Loại href file/javascript/data và URL sai cú pháp | Đạt |
| Khởi động | Qt/Chromium và thao tác dán/copy định dạng trong tiến trình riêng | Đạt trên Linux; bản Windows kiểm tra qua workflow |

Các ca mới: `tests/test_richtext.py`. Ca đóng gói `facebook_helper/smoke.py` kiểm tra dán HTML đậm/màu/danh sách, copy HTML, bốn tab, Chromium và thoát sạch. Workflow Windows dùng plugin cửa sổ native `windows`, không dùng Qt offscreen, để kiểm tra clipboard Windows thực tế.

Lỗi sửa trong quá trình kiểm tra: bảng được chèn nhưng con trỏ còn ở ngoài bảng; định dạng cũ còn sau xóa nội dung và dán chữ thuần; khoảng trắng giữa các đoạn HTML tạo khoảng trắng thừa khi dán; dọn clipboard của fixture offscreen trước khi kết thúc pytest.

Cần kiểm tra thêm với clipboard thật của từng phiên bản Word/Chrome trên máy người dùng: bảng phức tạp, ảnh nhúng, font chưa cài và CSS trang nguồn. Không cam kết giữ mọi bố cục Word/CSS. Các kiểm thử ở đây không xác nhận định dạng nào được Facebook chấp nhận khi dán; tự điền hiện dùng chữ thuần.

## Bản Windows đã xác nhận

Workflow [Build Windows #43856857520](https://github.com/Trung27012003/facebook-helper/actions/runs/43856857520) thành công ở mã `57dd0a4ee9a7f1d2033eab99fac79501449d9269`. Chạy file `.exe` với `QT_QPA_PLATFORM=windows`: `ok=true`, `rich_paste_and_copy=true`, `qt_started=true`, `worker_stopped=true`. Đây là kiểm tra clipboard Qt native Windows, không chỉ mô phỏng offscreen.

[Tải 0.3.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.3.0), ZIP 445.896.811 byte. SHA256: `3dab29223ee5dd5313c4fc8502a2d5e37c2e85f7e6fdcd2aafd6ff3d2ce3c060`. CI mã nguồn cũng thành công.

HTML dùng trong kiểm tra đại diện cho các kiểu định dạng hỗ trợ; chưa phải kiểm tra trực tiếp từng phiên bản Word hoặc định dạng được Facebook chấp nhận.
