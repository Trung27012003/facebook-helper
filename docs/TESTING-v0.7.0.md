# Kiểm thử 0.7.0

Ngày 17/11/2026 (giờ Việt Nam). **180 passed, 113.15 giây** trên mã phát hành `b63402aecc0a6c1d2b25e830106be05f9e0717d4`: [Checks #44019641501](https://github.com/Trung27012003/facebook-helper/actions/runs/44019641501), [log](test-output-v0.7.0.txt). Ruff đạt. Nhóm beginner/queue/packaging chạy riêng: **33 passed, 15.79 giây**, [log](test-ui-v0.7.0.txt).

| Luồng | Bằng chứng kiểm tra |
|---|---|
| Bốn bước | Chọn bài → nhóm → xem lại → gửi. Không tạo/gửi trước bước cuối; chỉ gửi một lần khi bắt đầu; đúng nhóm và thứ tự |
| Kiểm tra lại trước gửi | Sửa bài sau xem lại sẽ chặn; bỏ xác nhận trùng không tạo đợt/gửi; thiếu bài/nhóm có hướng dẫn |
| Nhiều đợt chờ | Dùng UI tạo sáu đợt cho hai bài/ba nhóm, không gọi trình duyệt; mở lại đợt để tiếp tục |
| Soạn/sửa từ luồng đăng | Mở đúng bài được chọn; không thay bài đang chỉnh sửa khi người dùng từ chối bỏ chỉnh sửa |
| Nháp | Giữ HTML, chữ Việt, ảnh và thứ tự, hashtag; tự lưu không cập nhật bài đã lưu hoặc lượt đăng |
| Khôi phục | Cửa sổ mới thấy nháp; khôi phục định dạng, không tự đăng/lưu bài vào thư viện; bắt đầu nháp khác không ghi mất nháp cũ |
| Đóng ứng dụng | Lưu nháp trước khi đóng, không hỏi bỏ nội dung; nếu ổ đĩa không ghi được thì giữ cửa sổ mở |
| Nháp thiếu ảnh | Không thay editor hiện tại, không bỏ journal nháp; báo lỗi để kiểm tra tệp |
| Ô tích | Chọn bằng Space/ô tích không Ctrl/Shift; chọn tất cả; giữ ô tích khi refresh và bỏ lựa chọn ẩn khi lọc |
| Kết quả và lọc | Bảng năm cột; ngày gửi thật cho Hôm nay; Cần xử lý lọc error/uncertain/sending; chi tiết giữ link, ghi chú, lịch sử |
| Hướng dẫn | Có thể ẩn hướng dẫn, lưu lựa chọn; mở lại từ đầu cửa sổ |
| Đóng gói | Smoke check Summernote, rich paste/copy, bốn bước, năm cột, journal nháp, Chromium, Qt và dừng worker |
| Hồi quy | Đăng nhiều nhóm, pending vẫn chuyển nhóm, dừng uncertain, chống trùng, theo dõi duyệt, SQLite, xuất Excel và sao lưu |

Đã xem ảnh giao diện ở 1280×850 và 980×680. Bảng kết quả không có cuộn ngang ở 980×680; nút tiếp tục/bắt đầu nằm ngoài vùng cuộn, nhìn thấy ở cạnh dưới cửa sổ. Ảnh minh họa dùng dữ liệu giả: [xem lại](images/review-v0.7.png), [kết quả](images/manager-v0.7.png).

Nháp lưu qua preferences trong SQLite hiện có, không thay schema bản 0.6. Bấm Lưu bài mới cập nhật bài có thể đăng; các lượt đã tạo vẫn giữ snapshot cũ. Nháp chưa hoàn tất có trong bản sao lưu DB; ảnh vẫn dùng thư mục ảnh đã nhập. Thay đổi ngay trước mất điện trong khoảng chờ 1,2 giây có thể chưa được lưu.

Các test Facebook chạy Chromium với trang mô phỏng; chưa xác minh trên tài khoản Facebook thật. Thay đổi này tập trung giao diện và nháp, không nâng mức bảo đảm phát hiện duyệt hay định dạng Facebook. Không có hẹn giờ đăng.

## Gói Windows

[Build Windows #44019642407](https://github.com/Trung27012003/facebook-helper/actions/runs/44019642407) thành công từ cùng mã phát hành. Chạy `.exe` với giao diện Windows thực xác nhận Chromium, Summernote, dán/copy HTML, bốn bước, bảng năm cột, tự lưu nháp, năm tab và dừng worker sạch. CI nguồn thành công trước khi phát hành.

[Tải 0.7.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.7.0). ZIP 620.975.679 byte; SHA256 công bố `7c36ce6b7962623f39a7631885d83a5dcb0eefcabcfdcb998a842eae45ecd122`. Đã đọc checksum và kiểm tra đầu tệp ZIP qua phản hồi tải HTTP 206, chữ ký ZIP đúng; không tải toàn bộ ZIP để tính lại hash ở máy này.
