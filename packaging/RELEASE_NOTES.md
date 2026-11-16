Bản **0.3.0** cho **Windows 10/11 64-bit**, có sẵn Chromium, không cần cài Python.

**Cách chạy:** tải `FacebookHelper-Windows-x64.zip` → giải nén toàn bộ → mở thư mục `FacebookHelper` → chạy `FacebookHelper.exe`. Giữ nguyên `_internal` đi kèm. Giữ dữ liệu bài, nhóm, nhãn và lịch sử từ các bản trước.

**Trình soạn thảo mới:**

- Thanh rich text với tiêu đề, đậm/nghiêng/gạch chân, font, cỡ chữ, màu/tô nền, danh sách và đánh số, căn lề, link, bảng, xóa định dạng và hoàn tác/làm lại.
- **Ctrl+V / Dán giữ định dạng** để nhập các định dạng hỗ trợ từ Word hoặc trang web khi clipboard có HTML.
- **Ctrl+Shift+V / Dán chữ thuần** để bỏ kiểu chữ nguồn.
- **Sao chép bài có định dạng** tạo clipboard gồm HTML và chữ thuần, kèm hashtag. Nơi nhận quyết định định dạng dùng được.
- Lưu/mở lại giữ định dạng. Thanh công cụ cập nhật theo vị trí con trỏ. Khi tự điền Facebook, giữ dấu đầu dòng và số thứ tự, bảng được chuyển thành các hàng chữ dễ đọc.

Tiếp tục có mẫu tuyển dụng, nhiều ảnh, nhãn nhóm, chọn một/nhiều nhóm/theo nhãn, danh sách đăng lần lượt và tùy chọn tự gửi có xác nhận.

**Giới hạn:** clipboard chỉ có chữ thuần sẽ không tự khôi phục được định dạng; font không có trên máy có thể hiển thị bằng font thay thế. Ảnh trong HTML dán không tự nhập, hãy dùng Thêm ảnh. Định dạng Word/CSS phức tạp có thể không giữ nguyên hoàn toàn. Tự điền Facebook dùng chữ thuần; Facebook quyết định kiểu chữ hiển thị.

Gói `.exe` được kiểm tra khởi động, dán/copy rich text và Chromium trên Windows trước khi phát hành. Test đăng bài dùng mô phỏng; **chưa xác nhận đăng Facebook thật**. Gửi xong không đồng nghĩa bài đã được duyệt.

Bản chưa ký mã số; Windows có thể cảnh báo nhà phát hành. `SHA256SUMS.txt` đi kèm để đối chiếu tính toàn vẹn.
