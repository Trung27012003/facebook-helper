**Facebook Helper 0.9.0 — giao diện gọn trên toàn ứng dụng**

- Soạn bài: thư viện bên trái, nội dung bên phải; nút Lưu nổi bật khi sửa, Chọn nhóm đăng nổi bật sau khi lưu. Đi thẳng đến chọn nhóm từ bài đang soạn.
- Thao tác bài và ảnh được gom vào menu; nút chính luôn ở cuối khung khi cuộn.
- Nhóm: kiểm tra link ngay khi nhập, chỉ bật Lưu khi hợp lệ và có thay đổi; giữ rõ nhóm đang chọn.
- Đăng bài: Bắt đầu / Tạm dừng / Xem kết quả theo trạng thái, hiện link trong bảng, bỏ hướng dẫn thừa. Hoàn tất thì không còn Bắt đầu.
- Bài đã đăng mặc định hôm nay; có Mở bài / Sao chép link / Mở nhóm. Xóa được tách khỏi thao tác chính.
- Cài đặt chia ba phần: Tài khoản, Dữ liệu, Hỗ trợ. Có Xuất chẩn đoán cục bộ, không xuất nội dung/cookie/token hoặc phản hồi thô.
- Sửa bộ lấy link để không đòi nội dung gửi đi giống hệt bản lưu; nhận request muộn và phản hồi GraphQL bổ sung, bỏ phản hồi từ request cũ.

Chưa có phiên Facebook thật để xác minh trên tài khoản người dùng. Nếu không có URL/mã bài được nhận diện thì chưa lấy được link; link chờ duyệt có thể chưa mở được.

Đóng bản cũ, giải nén toàn bộ ZIP vào thư mục mới rồi chạy FacebookHelper/FacebookHelper.exe. Không cần cài Python; dữ liệu cũ được giữ, schema 6.
