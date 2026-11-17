# Kiểm thử 0.8.0

Ngày 17/11/2026 (giờ Việt Nam).

## Phạm vi thay đổi

- Trang Bài đã đăng chỉ có đợt đăng, hai ngày, từ khóa và Tìm kiếm. Không tự tìm khi đang nhập; Enter áp dụng bộ lọc.
- Bảng hiển thị link và kết quả gửi ngắn gọn, không phụ thuộc duyệt. Mở bài/Sao chép link dùng dòng đang chọn; thiếu link thì tắt nút. Xuất Excel dùng kết quả tìm kiếm.
- Bỏ lịch sử và kiểm tra duyệt trên trang này; tắt bộ hẹn giờ kiểm tra, kể cả cấu hình từng bật từ bản cũ. Không xóa dữ liệu cũ.
- Lấy link từ phản hồi của đúng thao tác gửi (đúng mutation, nội dung, nhóm) hoặc từ bài mới đúng nội dung; không dựng link từ ID không rõ loại. Chạy cả với bài chờ duyệt. Hỗ trợ permalink `pfbid`.
- Link được lưu trước khi tự chuyển nhóm. Thiếu link vẫn tiếp tục; kết quả gửi chưa rõ thì giữ link đã xác minh và dừng để tránh trùng.

## Các nhóm kiểm thử

| Nhóm | Các tình huống chính |
|---|---|
| Tìm kiếm | Phải bấm tìm/Enter; làm mới không áp dụng từ khóa đang sửa; nhiều đợt cùng bài/nhóm không lẫn; tên đợt có thể tìm bằng từ khóa |
| Khoảng ngày | Hai đầu được bao gồm, ngoài khoảng bị loại; ngày gửi được ưu tiên; lần thử gửi không bị ghi thành gửi thành công; khoảng ngược được báo |
| Link và Excel | Sao chép đúng dòng; mở/copy tắt khi thiếu link; xuất đủ kết quả đang tìm, không lệ thuộc dòng được chọn; hủy xuất/không kết quả không tạo tệp |
| Phản hồi gửi | Chỉ đọc phản hồi thao tác vừa gửi trong chính trình duyệt; sai nhóm/nội dung/mutation bị bỏ qua; JSON lỗi/không rõ cấu trúc/mơ hồ không tạo link; gỡ listener sau thao tác |
| Tự chuyển nhóm | Bài chờ duyệt có hoặc không link đều tiếp tục; lưu link trước khi chuyển; không chạy kiểm tra duyệt; trạng thái chưa rõ dừng |
| Hồi quy | Nháp, UID, Summernote, HTML, ảnh, CRUD, sao lưu, phiên trình duyệt, chống trùng, đóng ứng dụng và đóng gói |
| Giao diện | Xem ảnh thật từ Qt ở 980×680 và 1280×850; bộ lọc và nút chính vừa cửa sổ |

[Ảnh 980×680](qa/v0.8.0/bai-da-dang-980.png) · [Ảnh 1280×850](qa/v0.8.0/bai-da-dang-1280.png).

Các test cho ô tích, nút lọc nhanh và kiểm tra duyệt trên giao diện cũ đã được thay bằng yêu cầu mới. Các báo cáo 0.7.x là lịch sử kiểm thử phiên bản cũ, không phải nghiệm thu giao diện 0.8.0.

## Giới hạn

Kiểm thử trình duyệt dùng Chromium và trang/phản hồi mô phỏng, không gửi Facebook thật. Cấu trúc phản hồi thật có thể thay đổi; không khẳng định mọi bài chờ duyệt đều cung cấp link. Chưa nghiệm thu với tài khoản Facebook thật hoặc người dùng mới. Ảnh giao diện được chụp Qt offscreen trên Linux, không phải bằng chứng DPI Windows.

## Kết quả tại workspace

`ruff check .` đạt. Bộ kiểm thử cuối: **253 passed trong 139,31 giây**, không failure/error/skipped. [JUnit](qa/v0.8.0/local-tests.xml). Một lỗi mới phát hiện khi mô phỏng hết chỗ lưu đã được sửa: việc tắt kiểm tra duyệt không còn ghi lại cấu hình mỗi khi hủy đóng cửa sổ vì nháp chưa lưu được. Ca hết chỗ lưu và bộ kiểm thử toàn bộ đã chạy lại đạt.

## CI mã nguồn

[Checks #44097261246](https://github.com/Trung27012003/facebook-helper/actions/runs/44097261246) đạt trên mã nguồn `80029aa1e5c63d12616587fb94812ad5693eea49`: Ruff và **253 test, 141,256 giây**, 0 failures/errors/skipped. [JUnit tải từ artifact CI](qa/v0.8.0/ci-tests.xml).

## Gói Windows

[Build Windows #44097261335](https://github.com/Trung27012003/facebook-helper/actions/runs/44097261335) đạt trên cùng mã nguồn. File `.exe` được chạy từ thư mục có dấu/khoảng trắng, kiểm tra Qt, Chromium, Summernote/dán-copy HTML, bốn bước, sáu cột kết quả, nháp và đóng worker. ZIP gồm 4.000 tệp; rà tên tệp không thấy dữ liệu/phiên người dùng thuộc danh sách cấm. [Bằng chứng](qa/v0.8.0/windows-verification.json).

[Tải bản 0.8.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.8.0). ZIP 620.967.666 byte. SHA256 công bố: `841fec0b4c65aba61e661a7b82647cb38f80771619edfdaa325b6c434c3dac7d`. Đã tải checksum và kiểm tra đầu ZIP từ link công khai: HTTP 206, chữ ký `504b0304`. Không tải toàn bộ ZIP để tính lại hash tại workspace.
