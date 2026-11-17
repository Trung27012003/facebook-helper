# Kiểm thử 0.6.0

Ngày 17/11/2026 (giờ Việt Nam). **165 passed, 111.60 giây** trên CI của mã phát hành `c353b60debffbd055bf914ea380ff894ef00b19f`: [Checks #44003018310](https://github.com/Trung27012003/facebook-helper/actions/runs/44003018310), [log](test-output-v0.6.0.txt). Ruff đạt. Kiểm tra riêng tracking/queue: [50 passed](test-tracking-v0.6.0.txt); sau bổ sung nhãn mâu thuẫn: [35 passed](test-inspection-v0.6.0.txt).

| Phần | Kiểm tra |
|---|---|
| Theo dõi trạng thái | Đúng link và nội dung; chờ duyệt, đã hiển thị, bị từ chối, bị gỡ; nhãn VN/EN |
| Không kết luận sai | Bài không thấy, sai link, nhiều bài giống nhau, bài trong modal; link mở riêng chưa có bằng chứng; Nhãn bài mâu thuẫn với tab đang chọn, Not approved/Unpublished và chữ phê duyệt trong nội dung/bình luận |
| Chưa có link | Chỉ nhận diện trong phần nội dung của chính bạn khi khớp nội dung và thời gian; không nhận bài cũ cùng nội dung |
| Tab kiểm tra riêng | Không thay đổi bản đang soạn; đóng tab tạm sau kiểm tra; không gửi hay xóa bài |
| Hàng đợi kiểm tra | Nhiều bài theo thứ tự; dừng không đọc bài sau; lỗi đăng nhập giữ trạng thái và dừng đợt; không chạy song song với đăng bài |
| Định kỳ | Chỉ lúc rảnh, ưu tiên lâu chưa kiểm tra, tối đa 20 bài/đợt; mặc định tắt |
| SQLite | Cập nhật kết quả/URL/thời gian/lịch sử nguyên tử; chưa xác minh không hạ trạng thái đã biết; không bịa ngày gửi cũ |
| Khôi phục | Lượt đang gửi chuyển uncertain khi mở giao diện; không thay đổi sending chỉ vì mở thêm kết nối Store; gửi một lần, tiếp tục bỏ qua lượt đã xử lý; giữ snapshot |
| Chống trùng | So nội dung và bytes ảnh kể cả đổi tên bài/đường dẫn ảnh; phân biệt nhóm; chặn tự gửi chéo task; đăng lại có xác nhận ở lượt mới |
| Quản lý | Từ khóa, trạng thái, nhóm, nhãn, bài; ngày gửi/tạo/kiểm tra bao gồm hai đầu; giữ lựa chọn nhiều dòng sau refresh; Excel theo bộ lọc và chống công thức |
| Hồi quy | Summernote, clipboard HTML, nhiều ảnh, upload, bài dài, tự chuyển nhóm, dừng khi gửi chưa rõ, sao lưu và đóng ứng dụng |

Dữ liệu từ bản cũ nâng schema từ 3 lên 4, thêm mốc thời gian, kết quả kiểm tra, lịch sử và cấu hình. Không suy ngược ngày gửi từ ngày tạo. Lịch sử bắt đầu ghi từ bản này; không tạo lịch sử giả cho bản cũ.

Các trang Facebook trong test được mô phỏng và chạy qua Chromium thật. Chưa thử bằng tài khoản Facebook thật. Kiểm tra chỉ đọc các phần trang đã tải; có thể chưa xác minh nếu Facebook đổi giao diện, thiếu link/timestamp, nội dung chưa tải đủ hoặc phiên đăng nhập hết hạn. Đã hiển thị là quan sát tại thời điểm kiểm tra, không đảm bảo bài tồn tại mãi hay xác định được người đã duyệt.

Groups API đã ngừng hỗ trợ: [Meta v19 changelog](https://developers.facebook.com/docs/graph-api/changelog/version19.0/). Chức năng theo dõi dùng phiên trình duyệt hiện tại, không có private GraphQL doc_id hard-code.

## Gói Windows

[Build Windows #44003018252](https://github.com/Trung27012003/facebook-helper/actions/runs/44003018252) thành công từ cùng mã phát hành. `.exe` chạy với giao diện Windows thực, xác nhận Chromium đi kèm, Summernote, dán/copy rich text, năm tab, khởi động Qt và dừng worker sạch. CI nguồn thành công trước khi cho phép phát hành.

[Tải 0.6.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.6.0). ZIP 620.947.931 byte; SHA256 công bố `f652df6ec6847343523b66cf02218219b80f6a871706ea4c58e023e74a6f64aa`. Đã đọc file checksum và kiểm tra đầu tệp tải ZIP: HTTP 206, chữ ký ZIP đúng. Không tải toàn bộ ZIP để tính lại hash tại máy này.
