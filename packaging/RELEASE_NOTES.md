**Facebook Helper 0.8.1 — xóa bản ghi và lấy link bài chờ duyệt**

- Nút Xóa trên Bài đã đăng: xóa dòng đang chọn hoặc các bài đã gửi trong kết quả lọc, có xác nhận số lượng. Không xóa bài Facebook, bài soạn hoặc nhóm. Giữ biên nhận nội bộ chống gửi trùng.
- Nhận link cả khi phản hồi gửi chỉ có mã bài hợp lệ, không có URL; hỗ trợ nhóm có tên khi xác minh được mã nhóm qua canonical. Không cần chờ duyệt.
- Chờ thêm tối đa 3 giây cho phản hồi gửi đang tải, không bấm Đăng lại. Mã người dùng, ID không rõ loại và phản hồi sai nhóm bị bỏ qua.

Link chờ duyệt có thể chưa mở được. Nếu Facebook không cung cấp mã/link hợp lệ, vẫn lưu Đã gửi và chuyển nhóm; không bảo đảm lấy link cho mọi bài. Kiểm thử dùng mô phỏng, chưa kiểm chứng tài khoản Facebook thật.

Đóng bản cũ, giải nén toàn bộ ZIP vào thư mục mới rồi chạy FacebookHelper/FacebookHelper.exe. Không cần cài Python. Dữ liệu cũ được giữ, schema nâng lên 6.
