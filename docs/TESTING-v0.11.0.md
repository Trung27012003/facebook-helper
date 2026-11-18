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

Ruff đạt. Kiểm thử đầy đủ tại workspace: **331 passed, 194,64 giây**. Nhóm kiểm thử vị trí/nhãn riêng: **15 passed**.

[Checks #44216917395](https://github.com/Trung27012003/facebook-helper/actions/runs/44216917395) đạt trên commit `3ca8ba359e4e22f54e9bc542dc8137271499337b`: **331 test, 202,363 giây**, 0 failures/errors/skipped. [JUnit CI](qa/v0.11.0/ci-tests.xml).

[Build Windows #44216917274](https://github.com/Trung27012003/facebook-helper/actions/runs/44216917274) đạt trên cùng commit. Bản portable và bản cài đều chạy được Qt, Summernote, Chromium đầy đủ, danh mục vị trí, bộ chọn nhiều vị trí/nhãn, schema 7 và 6 tab. Kiểm tra cài/chạy/gỡ từ đường dẫn Windows có dấu đạt; DB và tệp đánh dấu dữ liệu người dùng còn nguyên sau gỡ.

[Phát hành v0.11.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.11.0):

| Tệp | Dung lượng | SHA-256 từ CI |
|---|---:|---|
| FacebookHelper-Setup-x64.exe | 326.471.944 byte | `149bb03fbd8390506533603191962788ed1c827815bf0bfd30ca5bcc2b007496` |
| FacebookHelper-Windows-x64.zip | 468.793.996 byte | `0c06081cd00fcd6a3229c076571489093279a9156a6a140712bd58963c781c18` |

Đã xác nhận ba asset ở trạng thái uploaded, đọc được SHA256SUMS công khai và chữ ký đầu tệp MZ/PK qua link tải. Hash trong bảng được lấy từ CI-generated SHA256SUMS, không tuyên bố băm lại toàn bộ tệp tải từ Internet. API Releases công khai được kiểm tra với updater thật: bản 0.10.0 nhận ra 0.11.0, bản 0.11.0 không báo cập nhật lại.

Audit 3.443 tệp không chứa dữ liệu người dùng. Prune bỏ 90.072.701 byte, còn 1.110.249.564 byte runtime. [Bằng chứng máy đọc được](qa/v0.11.0/release-verification.json).
