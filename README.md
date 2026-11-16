# Facebook Helper · HR

Ứng dụng desktop tiếng Việt cho **một người dùng**, hỗ trợ chuẩn bị tin tuyển dụng trên nhóm Facebook. Công nghệ: **Python + PySide6 + Playwright + SQLite**.

## Tải bản chạy sẵn cho Windows

**[Tải FacebookHelper-Windows-x64.zip](https://github.com/Trung27012003/facebook-helper/releases/latest/download/FacebookHelper-Windows-x64.zip)** · [Trang phát hành và SHA256](https://github.com/Trung27012003/facebook-helper/releases/latest)

Dành cho **Windows 10/11 64-bit**. Giải nén toàn bộ ZIP, mở thư mục `FacebookHelper`, nhấp đúp **`FacebookHelper.exe`**. Không cần cài Python hay Chromium riêng. Giữ nguyên thư mục `_internal`; không chạy ứng dụng trực tiếp bên trong file ZIP. Có hướng dẫn tiếng Việt trong `HUONG-DAN.txt` đi kèm.

Bản portable chưa ký mã số. Xem thông tin kiểm tra Windows và giới hạn Facebook ở trang phát hành.

## Bản 0.1 có gì?

- Kho bài tuyển dụng: lưu, tìm, nhân bản, xóa; font, cỡ chữ, màu, in đậm/in nghiêng trong bản nháp.
- Bài có nhiều ảnh, xem trước ảnh, sắp xếp thứ tự, hashtag cuối bài. Ảnh được sao chép vào thư mục dữ liệu nên không phụ thuộc ảnh gốc.
- Nhóm Facebook: tên, link, khu vực/ngành nghề, quy định và ghi chú.
- Tạo lượt đăng, cảnh báo nếu bài đã có lịch sử trong cùng nhóm. Nội dung và danh sách ảnh được chốt tại thời điểm tạo lượt.
- Trình duyệt riêng để đăng nhập, mở nhóm, điền cửa sổ tạo bài đang mở và tải nhiều ảnh lên. **Bạn tự kiểm tra và bấm Đăng trên Facebook.**
- Trạng thái riêng: chưa chuẩn bị, đã chuẩn bị, chờ duyệt, đã hiển thị, bị từ chối, có lỗi. Trạng thái do người dùng xác nhận; không tự suy luận bài đã được duyệt.
- Lấy permalink từ bài đang mở trong trình duyệt, lưu/copy link, mở link, chụp vùng trình duyệt đang hiển thị và xem ảnh minh chứng.
- Xuất Excel; sao lưu ZIP chứa cơ sở dữ liệu, ảnh bài viết và ảnh minh chứng.
- Nếu tự động điền không tương thích: sao chép nội dung, mở thư mục chỉ chứa ảnh của lượt đăng để tải thủ công.

**Giới hạn:** định dạng Word chỉ được giữ trong bản nháp; Facebook nhận nội dung chữ thuần. Chưa có AI, hẹn giờ, thiết kế poster, tự tìm bài mới trên bảng tin hoặc tự phát hiện phê duyệt. Đây là ứng dụng độc lập, không phải sản phẩm chính thức của Meta. Giao diện Facebook có thể đổi và cần cập nhật selector. Không có cơ chế vượt CAPTCHA/hạn chế tài khoản hoặc cam kết tránh khóa tài khoản.

## Cài và chạy trên Windows

Cài [Python 3.11+](https://www.python.org/downloads/) và Git, rồi mở PowerShell tại thư mục muốn chứa dự án:

```powershell
git clone https://github.com/Trung27012003/facebook-helper.git
cd facebook-helper
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m facebook_helper
```

Lần sau chỉ cần chạy lệnh cuối. Có thể dùng `start.bat` sau khi cài xong.

## macOS / Linux

```bash
git clone https://github.com/Trung27012003/facebook-helper.git
cd facebook-helper
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m playwright install chromium
.venv/bin/python -m facebook_helper
```

Linux cần môi trường desktop và thư viện hệ thống cho Qt/Chromium. Playwright có hướng dẫn dependency tại https://playwright.dev/python/docs/browsers#install-system-dependencies. Không dùng chế độ headless để đăng nhập tài khoản cá nhân.

## Quy trình đăng bài

1. Trong **Bài tuyển dụng**, tạo nội dung, hashtag, chọn/sắp xếp ảnh rồi **Lưu bài**. Tiêu đề quản lý không được đưa vào nội dung đăng.
2. Trong **Nhóm Facebook**, lưu nhóm bạn muốn sử dụng.
3. Trong **Đăng bài & minh chứng**, chọn bài và nhóm rồi **Tạo lượt đăng**. Mỗi lượt chỉ ứng với một bài và một nhóm. Muốn một bài đăng nhiều nhóm, tạo một lượt cho từng nhóm. Có thể lưu nhiều lượt cho nhiều bài khác nhau và thực hiện lần lượt.
4. **Đăng nhập Facebook**: tự đăng nhập trong trình duyệt được mở. Ứng dụng không có ô nhập mật khẩu.
5. **Mở nhóm** → trên Facebook tự mở cửa sổ **Tạo bài viết** → quay lại ứng dụng bấm **Điền bài**. Nếu ô đã có nội dung, ứng dụng dừng để tránh ghi đè. Khi cần, mở mục Ảnh/video trong cửa sổ soạn trước khi điền.
6. Kiểm tra trên Facebook, chờ ảnh tải xong và **tự bấm Đăng**. Ghi nhận **Chờ duyệt** nếu bài chưa hiển thị.
7. Khi bài hiển thị, lấy link từ thời gian đăng hoặc menu bài. Dán vào ứng dụng và **Lưu link**, hoặc mở bài cụ thể trong trình duyệt do ứng dụng quản lý rồi bấm **Lấy link đang mở**. Link phải trỏ đến bài cụ thể trong cùng nhóm, ví dụ `/groups/123/posts/456/`. Nếu Facebook dùng tên nhóm và ID khác nhau, hãy dùng cùng dạng định danh với link nhóm đã lưu.
8. **Mở link bài**, tự kiểm tra nội dung và vị trí cuộn rồi **Chụp màn hình**. Ảnh chỉ là vùng đang hiển thị, không phải toàn bộ trang; dùng **Xem ảnh minh chứng** để kiểm tra. Nếu chưa đăng nhập hoặc bài chưa tải, hãy đợi/đăng nhập và mở lại link trước khi chụp.
9. Chọn **Đã hiển thị** và xác nhận chỉ sau khi thực sự thấy bài. Chụp ảnh hoặc điền thành công không tự đổi thành đã đăng.
10. **Copy link** hoặc **Xuất Excel** để báo cáo. Excel chứa đường dẫn ảnh tương đối; khi chia sẻ minh chứng hãy gửi kèm ảnh từ thư mục dữ liệu hoặc bản sao lưu.

Khi đổi link sang một bài khác, liên kết ảnh minh chứng cũ được bỏ và trạng thái đã hiển thị cần xác nhận lại; file ảnh cũ vẫn được giữ.

## Dữ liệu và phiên đăng nhập

Trong tab **Dữ liệu & hướng dẫn**, có đường dẫn và nút mở thư mục dữ liệu:

- Windows: `%LOCALAPPDATA%\FacebookHelper` (đường dẫn thực tế trong ứng dụng là nguồn chính xác).
- macOS: `~/Library/Application Support/FacebookHelper`.
- Linux: `~/.local/share/FacebookHelper`.

Các thư mục: `helper.db` (SQLite), `images/`, `evidence/`, `browser/` (phiên Facebook). Có thể chạy `python -m facebook_helper --data-dir /duong/dan/rieng` để dùng dữ liệu thử nghiệm riêng.

**Không commit hoặc chia sẻ thư mục `browser/`** vì chứa dữ liệu phiên đăng nhập. Sao lưu ZIP của ứng dụng cố ý không chứa thư mục này. Muốn đăng xuất, dùng chức năng Đăng xuất trên Facebook trong trình duyệt riêng. Muốn xóa hoàn toàn phiên: đóng ứng dụng rồi xóa thư mục `browser/` trong thư mục dữ liệu.

Để khôi phục: đóng ứng dụng; sao lưu thư mục dữ liệu hiện tại; giải nén bản ZIP do chính ứng dụng tạo (gồm `helper.db`, `images`, `evidence`) vào thư mục dữ liệu; mở lại ứng dụng. Máy mới cần đăng nhập lại. Chỉ mở một phiên ứng dụng trên cùng thư mục dữ liệu.

Ảnh đã bỏ khỏi bản nháp vẫn được giữ để không làm hỏng lịch sử cũ. Bản đầu chưa tự dọn ảnh không sử dụng. Ảnh xuất tạm để đăng thủ công nằm trong thư mục tạm hệ điều hành, tên bắt đầu `facebook-helper-images-`; có thể xóa sau khi dùng.

## Phát triển và kiểm tra

Xem **[danh sách kiểm thử và kết quả](docs/TESTING.md)**: 60 test tự động, các lỗi đã sửa và các ca cần kiểm tra trên Facebook thật/Windows.

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
ruff check .
QT_QPA_PLATFORM=offscreen pytest -q
```

PowerShell: dùng `$env:QT_QPA_PLATFORM = 'offscreen'` trước khi chạy `pytest -q`.

Các test kiểm tra dữ liệu SQLite, bản nội dung lịch sử, permalink, chống công thức trong Excel, sao lưu, UI Qt và thao tác điền trên trang HTML mô phỏng bằng Chromium. **Test mô phỏng không xác nhận tương thích với Facebook thật.** Cần kiểm tra thủ công với tài khoản và nhóm được phép dùng; ứng dụng không đăng bài thật trong test.

## Đóng gói Windows

Workflow **Build Windows** chạy thủ công ở tab Actions, tạo ZIP chứa ứng dụng `.exe`, README và Chromium, không cần cài Python trên máy dùng. Hoặc chạy trên Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[build]'
$env:PLAYWRIGHT_BROWSERS_PATH = '0'
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onedir --name FacebookHelper --collect-all playwright --collect-all facebook_helper launcher.py
```

Mở `dist\FacebookHelper\FacebookHelper.exe`. Phải giữ nguyên cả thư mục `FacebookHelper`, không chỉ lấy file `.exe`. Bản đóng gói cần được thử trên Windows trước khi phân phối.
