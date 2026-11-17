# Kiểm thử 0.10.0

Ngày 17/11/2026, giờ Việt Nam. Schema dữ liệu giữ ở 6.

## Thử lại khi đăng

Tối đa 3 lần tổng cộng cho một thao tác. Lỗi kết nối/chờ sẵn sàng trước gửi có thể thử lại. Nếu bản soạn đã chuẩn bị xong, dùng publish_current cho chính bản đang mở, không dán chữ hoặc tải ảnh lại. Bản chưa hoàn tất chuẩn bị được giữ để kiểm tra, không tự gửi thiếu ảnh/chữ. Hết lần thử thì dừng.

Sau click, không thử lại nếu kết quả chưa rõ. Chỉ cho thử lại khi phản hồi của request bắt đầu trong thao tác này trả `data.story_create=null` và mọi error đều `is_transient=true`, bản soạn vẫn hiện và nút Đăng bật. Không có phản hồi đó, có dấu hiệu đã tạo story hoặc lỗi xác thực/hạn chế thì không click lại. Chỉ đóng popup lỗi tạm thời tương ứng; không đóng cảnh báo hạn chế/xác thực.

Các ca gồm: lỗi trước gửi rồi thành công lần 3; kết quả click không rõ chỉ click 1 lần; dùng bản soạn có sẵn thay vì điều hướng/dán lại; phản hồi lỗi tạm thời rồi thành công lần 2; cả 3 lần đều bị từ chối; auth/hạn chế/tệp sai không tự thử lại. Chromium dùng trang/phản hồi mô phỏng, chưa tái hiện tài khoản Facebook thật.

## Ngày, hiệu năng và bộ cài

DatePicker dùng QPushButton và QCalendarWidget tiếng Việt của Qt, không thêm thư viện web nặng. Bấm cả ô để chọn, tuần bắt đầu Thứ 2, có Hôm nay, popup nằm trong màn hình. Không nhập theo từng đoạn ngày/tháng/năm. [Ô ngày](qa/v0.10.0/date-fields.png), [Lịch](qa/v0.10.0/calendar.png).

Playwright worker khởi động theo lệnh đầu tiên, không chạy Node khi chỉ soạn bài. Smoke test xác nhận trạng thái lười khởi tạo rồi khởi động worker để kiểm tra đóng thực sự. Qt WebEngine vẫn cần cho Summernote; không tuyên bố loại bỏ hoàn toàn mức dùng RAM của trình soạn thảo.

Gói Windows cài Chromium `--no-shell`; smoke test dùng browser đầy đủ qua channel chromium. Prune chỉ chạy trên dist có FacebookHelper.exe: bỏ headless shell thừa, .js.map/.d.ts, .pak ngôn ngữ ngoài vi/en-US/en-GB. Giữ mã runtime và LICENSE. Có audit trước/sau, test xác nhận tài nguyên cần thiết còn nguyên. Đã dọn 1.769.938 byte cache/build phát triển trong workspace; không dọn dữ liệu/phiên người dùng.

Setup dùng Inno Setup, per-user, cùng AppId cho các bản sau, thư mục chương trình tách dữ liệu. Gỡ cài đặt không xóa SQLite, ảnh hay phiên Facebook. CI sẽ kiểm tra chạy từ bản portable, cài Setup vào đường dẫn có dấu, chạy lại app đã cài, gỡ và xác nhận DB/tệp dữ liệu còn nguyên. Số liệu dung lượng công bố sau khi tạo gói.

## Cập nhật

[Ảnh Cài đặt](qa/v0.10.0/settings-updates.png). QNetworkAccessManager kiểm tra Releases công khai bất đồng bộ, timeout 10 giây, giới hạn 2 MiB. Không cần token. So sánh version theo ba số, bỏ draft/prerelease, chỉ nhận đúng asset Setup đang uploaded từ đúng repo/tag/HTTPS. Không chấp nhận URL ngoài repo.

Auto kiểm tra khi mở, tối đa một lần/ngày; timer kiểm tra định kỳ khi app còn mở, nút thủ công có thể kiểm tra ngay. Hoãn thông báo khi đang thao tác Facebook/đăng. Hỏi Tải bộ cài/Để sau; chỉ mở trình duyệt khi đồng ý. Không tự tải ngầm hoặc tự cài. Dùng Qt TLS; smoke test kiểm tra SSL backend được đóng gói.

Máy đang dùng bản chưa có checker phải cài 0.10.0 một lần. Không thể gửi thông báo ngược vào binary cũ hoặc khi ứng dụng không chạy. Các ca so sánh 0.9/0.10, URL sai, bản thử nghiệm, callback bất đồng bộ, throttle, hoãn khi đang đăng và chỉ mở link sau đồng ý đều được kiểm tra với phản hồi giả, không gọi GitHub thật trong unit tests.

## Kiểm thử workspace

Ruff đạt. Một lượt toàn bộ trước hai bổ sung cuối: 314 passed trong 222,44 giây. Sau đó thêm lazy worker và giới hạn 3 click cho lỗi lặp; nhóm cuối 13 ca UI/ngày/cập nhật/đóng gói và 3 ca retry trình duyệt đạt. Tổng hiện tại 316; kết quả CI trên commit phát hành là kiểm tra đầy đủ cuối.

## Giới hạn

Chưa có phiên Facebook thực tế của người dùng. Không bảo đảm mọi lỗi có thể tự thử lại hoặc mọi bài chờ duyệt có link mở được. Thông báo cập nhật dùng API công khai, có thể thất bại khi mạng hoặc API giới hạn; có kiểm tra thủ công. Gói chưa ký mã số. Ảnh Qt offscreen không thay kiểm thử mọi DPI Windows.
