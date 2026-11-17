**Facebook Helper 0.7.1 — sửa lỗi phát hiện khi kiểm thử checklist**

Đóng bản cũ, sao lưu dữ liệu rồi giải nén toàn bộ ZIP vào thư mục mới và chạy `FacebookHelper/FacebookHelper.exe`.

Đã sửa bốn lỗi được tái hiện bằng kiểm thử:

- Khôi phục nháp có thể nhận nhầm một bài mới dùng lại mã số bài đã xóa. Bài được bổ sung định danh ổn định; chỉ nối lại nháp khi đúng bài gốc. Nháp từ bản cũ thiếu định danh sẽ mở thành bài mới để giữ nguyên các bài đã lưu.
- Tìm kiếm thư viện bài chỉ đọc 250 ký tự đầu. Nay tìm toàn bộ nội dung và hashtag.
- Hoàn tác sau khi nạp bài có thể quay về rỗng hoặc nội dung bài trước. Nay lịch sử Summernote bắt đầu lại ở nội dung vừa nạp.
- Sau gửi, bài mới khác nội dung nhưng trùng tiêu đề có thể bị nhận nhầm link. Nay chỉ bổ sung kết quả hiển thị khi nội dung phù hợp; thiếu bằng chứng giữ đã gửi. Không thêm chặn so khớp ký tự vào bước đăng.

Giữ giao diện bốn bước, ô tích, tự lưu nháp, tự chuyển nhóm và theo dõi trạng thái của 0.7.0. Dữ liệu được nâng schema từ 4 lên 5 để lưu định danh bài; bài, ảnh và lịch sử được giữ.

Bộ kiểm thử đã được mở rộng theo checklist, có JUnit và kết quả từng ca riêng. Kiểm tra Windows thêm đường dẫn chương trình có dấu/khoảng trắng và rà tệp dữ liệu trong ZIP. Các ca Facebook thật, Microsoft Word, DPI và nghiệm thu người dùng chưa đủ điều kiện được ghi rõ trong báo cáo; không suy diễn mô phỏng thành đã nghiệm thu Facebook thật.

Bản chưa ký mã số; checksum đi kèm.
