# Kiểm thử bản 0.4.1: đối chiếu nội dung trong ô Facebook

Ngày 16/11/2026 (Asia/Saigon). **116/116 test đạt**, 69.65 giây. Log: [test-output-v0.4.1.txt](test-output-v0.4.1.txt).

Báo cáo người dùng: bài có đủ chữ phía trên ảnh, nhưng ứng dụng dừng với lỗi “Nội dung trong ô Facebook khác bài đã lưu sau khi dán”. Tùy chọn ứng dụng bấm Đăng đang bỏ chọn.

Đã tái hiện ba ca false positive trong mô phỏng trước khi sửa: cùng chữ tiếng Việt có Unicode NFC/NFD khác nhau; marker số thứ tự được đọc khác nhau; đọc trạng thái trung gian khi Facebook chưa cập nhật xong. Lượt chạy trước sửa: **3 lỗi, 1 đạt** (ca thiếu chữ thật vẫn phải bị chặn).

Sửa:

- Chuẩn hóa Unicode và dấu định dạng vô hình; xử lý marker trên cả bản lưu và nội dung đọc lại, giữ số trong lương/ngày/liên hệ.
- Đọc văn bản qua DOM/Range/nội dung hiển thị; bỏ điều khiển ảnh không thuộc bài khi đối chiếu.
- Chờ nội dung và định dạng ổn định qua hai lần đọc; không chỉ chờ ô có một ký tự rồi so ngay.
- Dán và xác nhận chữ trước khi đính kèm ảnh; xác nhận lại sau đính kèm, kể cả ô soạn bị tạo lại.
- Không dán lại, không ghi đè bản người dùng đang soạn khi đối chiếu lỗi.
- Báo bước tiếp cho bài đã chuẩn bị: kiểm tra chữ/ảnh rồi bấm Đăng trên Facebook; số phiên bản hiện trên tiêu đề cửa sổ.

Các ca mới trong `tests/test_browser.py`: Unicode tương đương; số danh sách; dán chậm; thiếu một đoạn; ảnh thêm điều khiển; ô soạn thay thế sau upload; sai số tiền. Các ca thiếu chữ và sai mức lương tiếp tục bị chặn trước khi Đăng.

Kiểm tra dùng Chromium với trang mô phỏng; chưa xác minh trên tài khoản Facebook thật của người dùng. Từ ảnh không xác định được chính xác ca nào gây lỗi ở máy người dùng, vì vậy không khẳng định một nguyên nhân cụ thể đã được chứng minh trực tiếp trên Facebook.

## Bản Windows

Workflow [Build Windows #43880797578](https://github.com/Trung27012003/facebook-helper/actions/runs/43880797578) thành công từ mã `82e59df3970263aad69dae31195ec16c674477b9`, gồm kiểm tra `.exe`, Summernote, clipboard và Chromium. CI mã nguồn thành công trước khi phát hành.

[Tải 0.4.1](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.4.1). ZIP 620.900.779 byte. SHA256: `243c300f6ad5daeaf05191a1e6ec7136ea685112bf91f4c0d07b7ba402ef1a29`.

Không đánh dấu kiểm tra trên tài khoản Facebook thật là đạt; các test luồng đăng vẫn sử dụng mô phỏng.
