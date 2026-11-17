# Kiểm thử 0.8.1

Ngày 17/11/2026 (giờ Việt Nam).

## Thay đổi

- Thêm một nút **Xóa**, có lựa chọn xóa dòng đang chọn hoặc các bài đã gửi trong kết quả đang lọc. Xác nhận số lượng trước khi gỡ. Lượt chưa gửi/đang chạy, bài soạn, nhóm và bài Facebook được giữ.
- Xóa khỏi danh sách bằng `hidden_at` (schema 6); giữ biên nhận lượt gửi nội bộ để tiến độ không chạy lại và cảnh báo trùng không mất. Dữ liệu cũ được nâng schema tại chỗ; không xóa tệp ảnh dùng chung. Bộ lọc đang sửa dở không thay đổi tập bản ghi sắp xóa.
- Sửa lấy link sau gửi khi phản hồi chỉ có `post_id`/`legacy_story_hideable_id`, URL trống. Chỉ đọc đúng phản hồi gửi và trường mã bài đã nhận diện, không dùng `story.id` không rõ loại, ID người dùng hoặc mã nhóm làm mã bài. Mã ghép chỉ được tách khi tiền tố khớp nhóm đã xác minh.
- Với nhóm dùng tên, chỉ nối mã nhóm số khi trang nhóm hiện tại cung cấp canonical/og:url hợp lệ. Không chấp nhận phản hồi nhóm khác. Tham khảo cách đọc trường mã bài trong [ví dụ công khai](https://github.com/rocky-bot-320/Messenger-goat-bot/blob/a2420c6b33f9a6a700587bd1a8069b9c03413c93/scripts/cmds/post.js); không gọi API riêng hoặc sao chép luồng đăng từ ví dụ.
- Chờ thêm tối đa 3 giây cho chính phản hồi gửi đang tải, không chờ duyệt hoặc gửi lại. Hủy listener ở cuối thao tác. Bài chờ duyệt có link vẫn giữ trạng thái gửi; không tự đánh dấu đã hiển thị.

## Kiểm thử

| Nhóm | Tình huống |
|---|---|
| Xóa | Từng dòng, toàn bộ kết quả lọc đã áp dụng, hủy xác nhận, không chạm Facebook, giữ link/biên nhận chống trùng, không chạy lại lượt đã gửi, chặn lượt đang gửi, cập nhật nguyên tử và mở lại dữ liệu |
| Link chờ duyệt | URL trực tiếp, chỉ `post_id`, chỉ `legacy_story_hideable_id`; nhóm số và nhóm tên đã xác minh qua canonical; lưu URL cũ không được lẫn vào kết quả mới |
| Phản hồi | Sai nhóm, sai nội dung, sai mutation, phản hồi lỗi, ID không rõ loại, nhiều mã mâu thuẫn, request đang tải hoặc trang đóng |
| Hồi quy | Soạn thảo, nháp, ảnh, CRUD, dữ liệu cũ, hàng đợi, tự chuyển nhóm, SQLite, sao lưu, xuất Excel và đóng gói |
| Giao diện | Qt offscreen 980×680 và 1280×850, bộ lọc và bốn nút thao tác nằm trong cửa sổ |

[Ảnh 980×680](qa/v0.8.1/bai-da-dang-980.png) · [Ảnh 1280×850](qa/v0.8.1/bai-da-dang-1280.png).

## Giới hạn

Không có phiên Facebook thật để tái hiện phản hồi của tài khoản người dùng. Lỗi bỏ qua trường mã bài và phản hồi đang tải được tái hiện bằng mô phỏng. Không khẳng định đây là toàn bộ nguyên nhân trên tài khoản thật. Cấu trúc phản hồi có thể thay đổi; nếu Facebook không cung cấp URL/mã bài hợp lệ thì chưa lấy được link. Link bài chờ duyệt có thể không truy cập được trước khi duyệt. Kiểm thử Chromium dùng trang/phản hồi mô phỏng; ảnh Qt offscreen không thay thế nghiệm thu DPI Windows hoặc tài khoản Facebook thật.

## Kết quả tại workspace

Ruff đạt. Bộ kiểm thử toàn bộ: **275 passed, 158,20 giây**, 0 failures/errors/skipped; [JUnit](qa/v0.8.1/local-tests.xml). Sau đó bổ sung xử lý và ca kiểm thử khi trang đóng lúc chờ phản hồi: chạy lại nhóm lấy link **23 passed**, gồm ca bổ sung này. Tổng bộ kiểm thử hiện tại là 276 ca; CI sẽ chạy toàn bộ trên commit phát hành.

## CI và thao tác giao diện

[Checks #44108180975](https://github.com/Trung27012003/facebook-helper/actions/runs/44108180975) đạt trên mã nguồn `dc03b4dac8705fdb362b87f9c881e157aa67dc05`: Ruff và **276 test, 161,825 giây**, 0 failures/errors/skipped. [JUnit CI](qa/v0.8.1/ci-tests.xml).

Kiểm tra thao tác Qt offscreen bổ sung: kích hoạt trực tiếp hai QAction trong menu Xóa, kiểm tra số lượng trong xác nhận, dòng biến mất, nút Xóa tắt khi hết kết quả và biên nhận gửi vẫn giữ. Đạt; kiểm tra này không được tính thêm vào 276 test CI và không phải kiểm tra giao diện Windows.

## Gói Windows

[Build Windows #44108180232](https://github.com/Trung27012003/facebook-helper/actions/runs/44108180232) đạt trên cùng mã nguồn. File `.exe` chạy từ thư mục có dấu/khoảng trắng, kiểm tra Qt, Chromium, Summernote/dán-copy HTML, bốn bước, sáu cột kết quả, nháp và đóng worker. ZIP gồm 4.000 tệp; rà tên tệp không thấy dữ liệu/phiên người dùng thuộc danh sách cấm. [Bằng chứng](qa/v0.8.1/windows-verification.json).

[Tải bản 0.8.1](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.8.1). ZIP 620.975.129 byte. SHA256 công bố: `70a51369dcd236467fdad114153d12e15131173f9f973492bce5540730a05ad8`. Đã tải checksum và kiểm tra đầu ZIP từ link công khai: HTTP 206, chữ ký `504b0304`. Không tải toàn bộ ZIP để tính lại hash tại workspace.
