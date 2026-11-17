**Facebook Helper 0.6.0 — Windows 10/11 64-bit**

Đóng bản cũ, sao lưu dữ liệu, giải nén toàn bộ ZIP vào thư mục mới rồi chạy `FacebookHelper/FacebookHelper.exe`. Giữ `_internal` đi kèm. Dữ liệu cũ được giữ và nâng cấp tự động.

- **Kiểm tra trạng thái sau đăng:** chọn một/nhiều bài hoặc toàn bộ kết quả đang lọc. Bật kiểm tra định kỳ khi ứng dụng mở nếu muốn (mặc định tắt, 30 phút/lần, tối đa 20 bài/đợt). Nhường trình duyệt khi đang đăng. Có nút Dừng kiểm tra.
- **Kết quả rõ ràng:** ngày gửi thực tế, lần kiểm tra gần nhất, lần đầu thấy bài hiển thị, lịch sử thay đổi và nguồn. Khi chưa đủ bằng chứng, giữ trạng thái đã biết và ghi Chưa xác minh được cho lần kiểm tra.
- **Chống trùng nội dung và ảnh:** cảnh báo cả khi lưu dưới tên bài khác; kiểm tra trước khi gửi qua nhiều task. Muốn đăng lại có chủ đích cần tạo lượt mới và xác nhận cảnh báo.
- **Tiếp tục sau gián đoạn:** khôi phục tiến độ và danh sách; lượt đang gửi chuyển sang chưa rõ kết quả, không tự gửi lại. Nút Tiếp tục danh sách còn lại đưa về phần chưa xử lý.
- **Quản lý dễ hơn:** tổng quan hôm nay, lọc bài/nhóm/nhãn/trạng thái, ngày gửi/ngày tạo/ngày kiểm tra; chọn nhiều bài, xuất Excel theo lựa chọn hoặc bộ lọc.

Luồng tự đăng liên tiếp, Summernote và lựa chọn nhóm theo nhãn được giữ. Không có chặn so khớp số ký tự sau dán.

Theo dõi dùng Playwright với phiên Facebook của bạn, không dùng Groups API đã ngừng hỗ trợ. Link mở được không tự coi là đã duyệt; không tìm thấy bài không tự coi bị xóa. Kiểm tra là best effort trên các phần trang đã tải. Chưa có link cần khớp nội dung và thời gian gửi; dữ liệu cũ thiếu ngày gửi không được suy ngược từ ngày tạo. Bài đã hiển thị có thể kiểm tra lại bằng tay.

Bộ kiểm thử tự động và kiểm tra gói Windows được chạy trước phát hành. Luồng Facebook được kiểm tra bằng trang mô phỏng, chưa xác minh trên tài khoản Facebook thật; giao diện thay đổi có thể làm kết quả chưa xác minh được. Không vượt hạn chế hay xác thực của Facebook. Bản chưa ký mã số; SHA256 đi kèm.
