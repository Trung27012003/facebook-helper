# Kiểm thử 0.5.0

16/11/2026 (Asia/Saigon). Bộ đầy đủ: **127 passed, 72.57 giây**. Sau thay đổi thanh tiến độ, nhóm test queue/manager: **18 passed, 9.15 giây**. Log: [toàn bộ](test-output-v0.5.0.txt), [queue và manager](test-queue-manager-v0.5.0.txt).

Đã kiểm tra tự chạy ba nhóm theo đúng thứ tự, gửi một lần cho từng nhóm, tự cập nhật trạng thái, bỏ qua bài đã gửi khi tiếp tục, dừng khi kết quả chưa rõ; không yêu cầu xác nhận giữa bài. Kiểm tra nhận diện bài mới cùng permalink và lưu status/url nguyên tử (không ghi published khi chưa có link). Giữ tạm dừng giữa thao tác và không tự chạy khi người dùng đã dừng.

Tab quản lý được kiểm tra từ khóa, trạng thái, khoảng ngày bao gồm cả hai đầu, khoảng ngày không hợp lệ. Bốn tab cũ và tab mới được kiểm tra khởi động/đóng qua smoke test (tổng năm tab).

Trạng thái tự động chỉ dựa trên bằng chứng quan sát: gửi hoàn tất → submitted; thông báo duyệt → pending; bài mới nhận diện được cùng link mới → published. Trạng thái không rõ phải dừng, không tự thử lại. Thu thập link là best effort, không lấy link cũ để giả thành bài mới.

Các test browser dùng Chromium với trang mô phỏng; chưa thử trên tài khoản Facebook thật. Không bảo đảm nhận diện mọi giao diện Facebook hoặc bài sẽ được phê duyệt. Tab ngày lọc theo ngày tạo lượt, giờ địa phương của máy.
