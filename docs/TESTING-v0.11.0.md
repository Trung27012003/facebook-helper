# Kiểm thử 0.11.0

Ngày 18/11/2026, giờ Việt Nam. Schema 7 thêm danh mục `positions` và bảng liên kết nhiều-nhiều `group_positions`. Các dữ liệu và bản chụp đợt đăng cũ được giữ nguyên; nhóm chưa phân loại có danh sách vị trí rỗng. Không tự đặt vị trí giả cho dữ liệu cũ.

## Các đầu mục và kiểm thử tự động

- Danh mục: thêm/sửa/xóa, chuẩn hóa tên Unicode và khoảng trắng, không phân biệt hoa/thường khi chống trùng; chặn tên rỗng và cập nhật ID không tồn tại.
- Liên kết nhóm: bắt buộc vị trí ở giao diện và SQLite Store; nhiều vị trí, nhiều nhãn, chống trùng liên kết; cập nhật nguyên tử, lỗi không để lại một phần dữ liệu. Vị trí không tồn tại không được lưu. Xóa nhóm gỡ liên kết; xóa vị trí đang dùng bị chặn. Sửa tên vị trí vẫn giữ liên kết qua ID.
- Chuyển schema 6 sang 7: giữ nhóm, nhãn, ghi chú, nội dung/link/trạng thái lượt cũ; nhóm cũ chưa có vị trí vẫn tìm được bằng nhãn, cần chọn vị trí trước khi lưu lại. Migration schema 1 cũng được chạy lại.
- Ô chọn Qt: bấm cả dòng hoặc ô tích chỉ đổi trạng thái một lần; tìm kiếm không làm mất lựa chọn; cập nhật tên/danh sách giữ các mục còn hợp lệ.
- Nhập nhóm: nút Lưu chỉ bật khi đủ tên, link hợp lệ và ít nhất một vị trí. Thêm nhanh vị trí giữ thông tin nhóm chưa lưu. Nhiều vị trí/nhãn lưu và mở lại đúng.
- Tạo đợt: nhiều vị trí hoặc nhiều nhãn dùng hợp các nhóm khớp, không có nhóm lặp; bỏ chọn thủ công được giữ khi làm mới; chưa chọn tiêu chí không có nhóm; tạo đợt chỉ lưu, chưa tự gửi. Tiếp tục qua bước xem lại trước khi chạy. Một nhóm/nhiều nhóm trực tiếp vẫn được kiểm thử.
- Bố cục: 6 tab và đường dẫn chuyển tab; nút Lưu nhóm còn nằm trong cửa sổ 980×680. [Danh mục](qa/v0.11.0/positions.png), [Nhóm](qa/v0.11.0/groups.png), [Ô chọn](qa/v0.11.0/position-picker.png), [Theo vị trí](qa/v0.11.0/batch-positions.png), [Theo nhãn](qa/v0.11.0/batch-tags.png).
- Hồi quy toàn bộ: Summernote, ảnh, SQLite, đợt đăng và chống gửi trùng, retry, lấy link, bộ lọc ngày, đăng nhập/đóng worker, cập nhật, đóng gói.
- Smoke đóng gói kiểm tra danh mục/ô chọn có sẵn, 6 tab, schema 7, Qt/Summernote/Chromium, TLS, clipboard, lịch, lazy worker và đóng không crash. Windows còn kiểm tra cài/chạy/gỡ, dữ liệu giữ nguyên.

## Giới hạn

Kiểm thử Facebook dùng trang và phản hồi mô phỏng, chưa dùng phiên Facebook của người dùng. Ảnh giao diện Qt offscreen không thay thế kiểm thử mọi mức DPI trên Windows. Gói chưa ký mã số.

## Kết quả

Đang chạy kiểm thử toàn bộ và tạo bộ cài Windows; kết quả CI và gói phát hành sẽ được ghi sau khi hoàn tất.
