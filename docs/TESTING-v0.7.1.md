# Kiểm thử bản sửa lỗi 0.7.1

Ngày 17/11/2026 (giờ Việt Nam). Bản 0.7.0 ban đầu đạt 180 test tự động khi chạy lại, nhưng các ca mới theo checklist đã tái hiện thêm bốn lỗi. Kết quả theo từng ca và giới hạn môi trường: [báo cáo 17/11/2026](TEST-RUN-2026-11-17.md), [Excel kết quả](TEST-RESULTS-2026-11-17.xlsx).

| Mã lỗi | Tình huống tái hiện | Cách sửa và kiểm tra lại |
|---|---|---|
| BUG-001 · P0 | Bài A bị xóa, SQLite dùng lại ID cho bài B; khôi phục nháp A nhận nhầm B | Thêm UID ổn định, schema 5; chỉ nối nháp với đúng UID. Nháp cũ không có UID mở như bài mới. Test xác nhận B không bị thay đổi, UID không dùng lại và nháp đúng bài vẫn cập nhật được |
| BUG-002 · P1 | Từ khóa nằm sau 250 ký tự đầu của nội dung không tìm thấy | Tách toàn bộ nội dung/hashtag khỏi tooltip rút gọn; kiểm tra từ khóa cuối bài |
| BUG-003 · P1 | Undo sau nạp bài đưa về rỗng; lịch sử có thể thuộc bài trước | Gọi API commit có sẵn của Summernote sau setContent; kiểm tra Undo/Redo và chuyển bài không lấy lại nội dung cũ |
| BUG-004 · P0 | Bài mới khác nội dung nhưng trùng tiêu đề được nhận thành bài vừa gửi | Đối chiếu nội dung trong bước nhận diện sau gửi, giữ submitted nếu không phù hợp; không chặn bước gửi theo số ký tự |

Các kiểm thử bổ sung bao gồm nháp/ảnh và thứ tự, backup nháp/lịch sử, khóa phiên thứ hai, CRUD, ảnh quá dung lượng, Excel chống công thức, ô tích xuất dữ liệu, ranh giới ngày, tìm kiếm nhiều trường, đường dẫn có dấu và các trường hợp giao diện. Kiểm tra tải dùng 200 bài, 250 nhóm, 1.000 lượt dữ liệu giả.

Những thay đổi cần phân biệt: các test mô phỏng gửi/kiểm tra trạng thái không gửi Facebook thật. Các ca cần tài khoản/nhóm Facebook, Word thật, DPI Windows và người dùng mới được ghi riêng; chưa đủ điều kiện không được đánh Đạt. Kiểm tra chạy lâu nhiều giờ được giữ ở Chưa chạy.

CI nguồn có JUnit; gói Windows kiểm tra `.exe` từ thư mục có dấu/khoảng trắng và rà manifest để chặn tệp dữ liệu/phiên người dùng. Kết quả chạy cuối và gói tải được ghi bên dưới.

## Kết quả cuối

[Checks #44056500774](https://github.com/Trung27012003/facebook-helper/actions/runs/44056500774): **236 passed, 118.37 giây**, 0 failures/errors/skipped; Ruff đạt. [JUnit](qa/2026-11-17/test-results.xml). Mã nguồn `36fa2c78fad870b3f6ba0762f2ef8d656895d418`.

[Windows #44056500275](https://github.com/Trung27012003/facebook-helper/actions/runs/44056500275) thành công: `.exe` chạy từ thư mục có dấu/khoảng trắng, Qt/Chromium/Summernote/nháp/worker đạt; ZIP 3.999 tệp qua rà dữ liệu/phiên theo tên tệp. [Bằng chứng](qa/2026-11-17/windows-verification.json).

Checklist: **144 Đạt trong phạm vi ghi từng ca, 35 Bị chặn, 1 Chưa chạy**. Chưa đủ để chốt nghiệm thu đầu-cuối Facebook thật. Không ánh xạ một-một 236 test với 180 ca checklist.

[Tải 0.7.1](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.7.1). ZIP 620.976.040 byte; SHA256 công bố `91dec0229937386a15c15e391ea16850dd61c0fa8945a167bbe78203d161b633`. Đã đọc checksum và kiểm tra đầu ZIP: HTTP 206, chữ ký ZIP đúng; không tải toàn bộ ZIP để tính lại hash tại máy này.
