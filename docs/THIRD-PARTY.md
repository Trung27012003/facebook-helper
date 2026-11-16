# Thư viện soạn thảo

Các bản phân phối nguyên bản được đóng kèm trong `facebook_helper/assets/vendor/`, không sửa file minified của thư viện. File `package.json` tại mỗi thư mục ghi phiên bản, nguồn npm và SHA512 integrity.

- **Summernote 0.9.1** — https://summernote.org/ — MIT. Thư viện cung cấp toolbar, lệnh chỉnh chữ, danh sách, bảng, codeview và fullscreen. Giấy phép trong `vendor/summernote/LICENSE`.
- **jQuery 3.7.1** — https://jquery.com/ — MIT. Dùng phiên bản tương thích với Summernote. Giấy phép kèm trong thư mục vendor.
- **DOMPurify 3.4.18** — https://github.com/cure53/DOMPurify — Apache-2.0 hoặc MPL-2.0. Dùng để làm sạch HTML dán/lưu; giấy phép nằm trong thư mục vendor.
- **Qt WebEngine / PySide6** — host trình soạn thảo trong desktop; không dùng nó để đăng nhập Facebook. Trình duyệt Facebook riêng vẫn do Playwright quản lý.

`assets/editor.js` là adapter clipboard/Qt và quy tắc bỏ nền tối; không tự dựng thanh nút định dạng. Thư viện không cần kết nối CDN khi sử dụng. Nội dung soạn không được gửi tới dịch vụ editor bên ngoài.
