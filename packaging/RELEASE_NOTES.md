Bản **0.2.0** cho **Windows 10/11 64-bit**, có sẵn Chromium, không cần cài Python.

**Cách chạy:** tải `FacebookHelper-Windows-x64.zip` → giải nén toàn bộ → mở thư mục `FacebookHelper` → chạy `FacebookHelper.exe`. Giữ nguyên `_internal` đi kèm.

Mới trong bản này:

- Mẫu bài tuyển dụng: tiêu đề, lời giới thiệu, công việc, yêu cầu, quyền lợi, địa điểm, lịch làm và liên hệ; thêm nhiều ảnh và xem trước.
- Nhãn nhóm: nhiều nhóm dùng chung nhãn, một nhóm có nhiều nhãn.
- Chọn một nhóm, tích nhiều nhóm hoặc chọn theo nhãn; bỏ nhóm không cần trước khi tạo danh sách.
- Nhiều danh sách cho nhiều bài; thực hiện từng nhóm theo thứ tự, theo dõi tiến độ, tạm dừng, tiếp tục và bỏ qua.
- Mặc định kiểm tra từng nhóm. Có tùy chọn **Tự bấm Đăng lần lượt**, yêu cầu xác nhận danh sách trước khi bắt đầu.
- Dừng khi chưa rõ kết quả gửi; không tự thử lại. Khôi phục sau lần tắt giữa lúc gửi cần kiểm tra để tránh trùng.
- Giao diện ba bước bằng tiếng Việt, nút đăng nhập dễ thấy; công cụ link/minh chứng nằm trong phần mở rộng.
- Tự nâng cấp dữ liệu 0.1, giữ bài, ảnh và lịch sử. Nên sao lưu ZIP trước khi cập nhật.

**Định dạng:** giữ tiêu đề, xuống dòng và các dòng `•` trong chữ thuần. Font/màu/đậm-nghiêng thuộc bản nháp; Facebook quyết định định dạng hiển thị. Ảnh tuyển dụng do người dùng tải lên.

Gói `.exe` đã qua kiểm tra tự động khởi động Qt và Chromium trên Windows. Tự động đăng đã được test với trang mô phỏng, **chưa kiểm tra đăng Facebook thật**; giao diện hoặc quyền nhóm có thể yêu cầu thao tác bằng tay. Gửi xong chưa đồng nghĩa được duyệt; người dùng kiểm tra, lấy link và lưu minh chứng sau.

Bản chưa ký mã số; Windows có thể cảnh báo nhà phát hành. `SHA256SUMS.txt` đi kèm để đối chiếu tính toàn vẹn.
