# Facebook Helper · HR

Ứng dụng desktop tiếng Việt cho một người dùng: soạn tin tuyển dụng theo mẫu, chọn nhóm bằng nhãn và thực hiện danh sách đăng lần lượt. **Python + PySide6 + Playwright + SQLite**.

## Tải về và mở ứng dụng

**[Tải bản Windows 10/11 64-bit](https://github.com/Trung27012003/facebook-helper/releases/latest/download/FacebookHelper-Windows-x64.zip)** · [Các bản phát hành](https://github.com/Trung27012003/facebook-helper/releases)

Giải nén **toàn bộ** ZIP → mở thư mục `FacebookHelper` → nhấp đúp `FacebookHelper.exe`. Không cần cài Python hay Chromium. Giữ nguyên `_internal` đi kèm, không chạy bên trong ZIP. Bản portable chưa ký mã số; thông tin kiểm tra và SHA256 nằm ở trang phát hành.

## Cách dùng bản 0.6.0 · Summernote

### 1. Soạn bài

- Chọn **Tạo bài theo mẫu tuyển dụng**. Điền vị trí, công ty, khu vực, thu nhập, công việc, yêu cầu, quyền lợi, địa điểm, thời gian và liên hệ. Mục không cần có thể để trống.
- Mẫu tạo tiêu đề, các phần **CƠ HỘI DÀNH CHO BẠN / YÊU CẦU / QUYỀN LỢI / ỨNG TUYỂN NGAY** và các dòng `•`, giống bố cục bài tuyển dụng tham khảo.
- Dùng **Summernote 0.9.1 nguyên bản** (thanh công cụ của thư viện), đóng kèm jQuery và DOMPurify, chạy offline trong Qt WebEngine. Không còn thanh nút rich text tự ghép.
- **Ctrl+V** từ Word/Facebook giữ các định dạng hỗ trợ. Khi dán từ Facebook, tự bỏ nền tối và màu chữ của giao diện để bài đọc được trên nền trắng; giữ đậm/nghiêng, tiêu đề, danh sách. Bản nháp Qt cũ có nền tối cũng được làm sạch khi mở.
- Thanh thư viện có font, cỡ, màu, đậm/nghiêng/gạch chân, danh sách, bảng, liên kết, mã HTML, fullscreen, undo/redo. **Ctrl+Shift+V** dán chữ thuần. **Sao chép bài có định dạng** sao chép HTML và chữ kèm hashtag.
- Ảnh trong nội dung dán không tự nhập; dùng **Thêm ảnh** để đính kèm. Nguồn chỉ có chữ thuần không thể tự khôi phục kiểu chữ.
- Sửa bài, thêm/sắp xếp ảnh, xem trước và lưu. Facebook chỉ hỗ trợ một phần định dạng; không hỗ trợ toàn bộ font/màu/bố cục Word.

### 2. Nhóm & nhãn

Thêm tên, link nhóm và ghi chú quy định. **Nhãn nhóm** dùng để chọn nơi đăng, không được chèn vào bài.

Ví dụ:

| Nhóm | Nhãn |
|---|---|
| Việc làm kỹ thuật Hà Nội | Hà Nội, Kỹ thuật |
| Cộng đồng tự động hóa | Hà Nội, Kỹ thuật |
| Việc làm kế toán | Hà Nội, Kế toán |

Một nhóm có thể có nhiều nhãn, ngăn cách bằng dấu phẩy. Nhiều nhóm dùng chung nhãn. Chọn nhãn **Kỹ thuật** sẽ chọn hai nhóm đầu; nhãn **Hà Nội** sẽ chọn cả ba. Nhãn khớp chính xác và không phân biệt hoa/thường, không tìm theo một phần tên. Có ô tìm nhóm theo tên/nhãn.

### 3. Đăng bài lần lượt

1. Bấm **Đăng nhập Facebook** ở đầu màn hình, đăng nhập trực tiếp trong trình duyệt riêng của ứng dụng. Phiên không dùng chung với Chrome cá nhân.
2. Chọn một bài đã lưu, rồi chọn **Một nhóm**, **Nhiều nhóm** hoặc **Theo nhãn nhóm**.
3. Kiểm tra danh sách đã tích; có thể bỏ bớt nhóm. Thứ tự thực hiện là từ trên xuống.
4. Đặt tên danh sách nếu muốn → **Tạo danh sách đăng**. Mỗi nhóm có một lượt riêng, giữ bản nội dung/ảnh tại thời điểm tạo. Có thể tạo nhiều danh sách cho nhiều bài khác nhau trước khi bắt đầu.
5. **Tự đăng bài** được bật sẵn. Bấm **Bắt đầu tự đăng**, xác nhận bài và nhóm: ứng dụng mở nhóm → dán HTML → đính kèm ảnh → chờ ảnh tải xong/nút Đăng sẵn sàng → tự bấm Đăng. Không so khớp nội dung hay số ký tự đọc lại; không có chặn “374/788”.
6. Nếu chỉ muốn chuẩn bị, bỏ chọn **Tự đăng bài**; nút bắt đầu đổi thành **Chỉ chuẩn bị bài**. Nếu Facebook đã có bản soạn đủ chữ/ảnh, dùng **Đăng bản đang mở** sau khi kiểm tra: gửi bản đó mà không dán/đính kèm lại. **Sau mỗi bài tự cập nhật trạng thái và chuyển nhóm tiếp theo** sau thời gian chờ đã chọn, không yêu cầu xác nhận từng bài.
7. **Không cần xác nhận giữa các nhóm.** Bài được ghi đã gửi, chờ duyệt khi Facebook có thông báo, hoặc đã hiển thị khi nhận diện được bài mới cùng link. Bài chờ duyệt không làm dừng danh sách. Lỗi hoặc chưa rõ kết quả sẽ dừng để tránh gửi trùng.
8. Xem thanh tiến độ để biết số nhóm đã xử lý. Có thể Tạm dừng/Tiếp tục/Bỏ qua. Tốc độ giữa nhóm được chỉnh ở ô thời gian chờ.

### Quản lý bài đăng

Tab **4. Quản lý bài đăng** có tổng quan hôm nay, số lượt còn lại/chờ duyệt/cần xử lý. Tìm từ khóa trong tiêu đề, nội dung, nhóm, ghi chú hoặc link; lọc theo bài, nhóm, nhãn nhóm, trạng thái. Chọn ngày tạo lượt, **ngày gửi thực tế** hoặc ngày kiểm tra để lọc khoảng ngày (giờ trên máy, gồm cả hai đầu). Ngày gửi được ghi khi ứng dụng gửi thành công hoặc bạn bấm xác nhận vừa gửi; chỉ sửa trạng thái không tự tạo ngày gửi. Lượt cũ chưa ghi ngày gửi sẽ không xuất hiện khi lọc ngày gửi; không lấy ngày tạo thay thế.

Giữ Ctrl/Shift để chọn nhiều dòng → **Kiểm tra bài đã chọn**, hoặc kiểm tra toàn bộ kết quả đang lọc. Có nút dừng kiểm tra, mở bài, copy link, xem lịch sử và xuất Excel cho bài đã chọn/kết quả đang lọc. Lịch sử ghi nguồn thay đổi, thời điểm, trạng thái cũ/mới và bằng chứng đọc được.

**Tự kiểm tra** mặc định tắt. Bật để kiểm tra định kỳ khi ứng dụng đang mở và không có danh sách đăng chạy; mặc định 30 phút, tối thiểu 5 phút. Mỗi đợt tối đa 20 bài đã gửi/chờ duyệt/chưa rõ kết quả, ưu tiên bài lâu chưa kiểm tra. Đã hiển thị/bị từ chối/bị gỡ có thể kiểm tra bằng tay. Lỗi truy cập hoặc đăng nhập dừng đợt kiểm tra và giữ nguyên trạng thái đã biết; kết quả lần kiểm tra là **Chưa xác minh được**.

Kiểm tra chạy trong tab trình duyệt riêng, dùng phiên hiện tại, không gửi lại/xóa bài. Ưu tiên đúng link + nội dung trong luồng thảo luận; tìm phần nội dung của chính bạn khi có liên kết phù hợp. Nếu chưa có link, cần khớp nội dung và thời gian gửi trong phạm vi 5 phút để tránh nhận nhầm bài cũ. Chỉ đọc các phần trang đã tải, tối đa ba lần cuộn luồng nhóm. Link truy cập được riêng lẻ không chứng minh đã duyệt; không tìm thấy bài không chứng minh bị gỡ. **Đã hiển thị** là bằng chứng quan sát tại lần kiểm tra, không phải cam kết bài sẽ luôn còn đó.

### Chống trùng và tiếp tục sau gián đoạn

Tạo danh sách/lượt mới sẽ cảnh báo nếu cùng nội dung (chuẩn hóa khoảng trắng) và cùng ảnh (so sánh bytes) đã có lượt trong cùng nhóm, kể cả lưu dưới tên bài khác. Có thể xác nhận tạo lượt để đăng lại có chủ đích. Trước khi tự gửi, ứng dụng kiểm tra lại các lượt đã gửi/chưa rõ kết quả ở danh sách khác; không gửi lại cùng lượt đã hoàn tất. Nhóm dùng ID và tên khác nhau chưa được tự ánh xạ với nhau.

Tiến độ, nội dung và thứ tự được lưu sau từng nhóm. Khi mở lại, lượt đang gửi được chuyển **Chưa rõ kết quả**; không tự gửi lại. Dùng **Tiếp tục danh sách còn lại**, kiểm tra các lượt chưa rõ rồi Bắt đầu / tiếp tục. Các lượt đã gửi/chờ duyệt/hiển thị được bỏ qua. Ứng dụng không tự bấm Đăng ngay lúc khởi động.


Link được lưu tự động khi nhận diện được link bài mới đúng nhóm; không lấy link bài cũ có sẵn trước lúc gửi. Nếu không nhận diện được, trạng thái giữ là đã gửi và link để trống, không tự bịa link hoặc đánh dấu đã hiển thị. Việc quản trị viên duyệt bài vẫn do nhóm quyết định.


**Không có bảo đảm tránh phát hiện, tránh kiểm duyệt hoặc tránh xóa bài.** Bài bị xóa có thể do nội dung, quy định nhóm, quản trị viên, trạng thái tài khoản hoặc nền tảng. Chưa xác minh nguyên nhân nếu không có thông báo thực tế. Các kiểm tra cảnh báo trong ứng dụng là hỗ trợ, không phát hiện được mọi trường hợp bài bị gỡ âm thầm.

### Link, ảnh minh chứng và báo cáo

Mở **Link bài, trạng thái & ảnh minh chứng** bên dưới bảng. Dán và lưu link bài, hoặc mở bài cụ thể trong trình duyệt của ứng dụng rồi **Lấy link đang mở**. Link cần thuộc cùng nhóm, dạng `/groups/ID/posts/ID/`; nếu Facebook dùng ID/tên nhóm khác nhau, hãy dùng cùng cách định danh với nhóm đã lưu.

**Mở link bài** → kiểm tra bài và vị trí cuộn → **Chụp màn hình** → **Xem ảnh minh chứng**. Ảnh chỉ là vùng đang hiển thị, không tự chứng minh bài đã được duyệt. Đổi sang permalink khác sẽ bỏ liên kết minh chứng cũ và yêu cầu xác nhận lại; file ảnh cũ vẫn được giữ.

**Xuất Excel** xuất lịch sử các lượt. Đường dẫn ảnh trong Excel là tương đối; gửi kèm ảnh/bản sao lưu khi cần chia sẻ minh chứng.

## Giao diện bản mới

![Soạn bài theo bố cục tuyển dụng](docs/images/editor-v0.4.png)

![Quản lý bài đăng, tìm từ khóa và lọc ngày](docs/images/manager-v0.6.png)

## Cập nhật, dữ liệu và sao lưu

Bản 0.4 giữ dữ liệu cũ và bổ sung HTML vào các lượt đăng mới, giữ bài, ảnh, nhóm và lịch sử cũ. Giải nén bản mới vào thư mục khác rồi chạy; dữ liệu nằm ngoài thư mục ứng dụng. Nên sao lưu ZIP trước khi cập nhật.

Tab **Dữ liệu & hướng dẫn** cho biết đường dẫn chính xác và có nút mở thư mục/sao lưu:

- Windows: thường `%LOCALAPPDATA%\FacebookHelper`.
- macOS: `~/Library/Application Support/FacebookHelper`.
- Linux: `~/.local/share/FacebookHelper`.

`helper.db` chứa bài/nhóm/nhãn/danh sách/lịch sử; `images/` chứa ảnh; `evidence/` chứa minh chứng; `browser/` chứa phiên Facebook. **Không chia sẻ hoặc commit `browser/`.** ZIP sao lưu cố ý không chứa phiên đăng nhập. Muốn xóa phiên, đóng ứng dụng rồi xóa thư mục `browser/` trong dữ liệu.

Khôi phục: đóng ứng dụng, sao lưu dữ liệu hiện tại, giải nén ZIP do chính ứng dụng tạo vào thư mục dữ liệu rồi mở lại. Máy mới cần đăng nhập Facebook lại. Ảnh không còn dùng vẫn được giữ để bảo toàn lịch sử. Ảnh xuất tạm để tải thủ công nằm trong thư mục tạm hệ điều hành với tiền tố `facebook-helper-images-`.

## Giới hạn thực tế

Chưa có AI, hẹn giờ, thiết kế poster, tự tìm permalink bài mới hay tự phát hiện phê duyệt. Tự động thao tác phụ thuộc giao diện/ngôn ngữ/quyền của nhóm Facebook và cần kiểm thử trên tài khoản thật. Không vượt CAPTCHA, hạn chế tài khoản hoặc bảo đảm tránh khóa tài khoản. Ứng dụng độc lập, không phải sản phẩm chính thức của Meta.

## Chạy từ mã nguồn

Windows (Python 3.11+ và Git):

```powershell
git clone https://github.com/Trung27012003/facebook-helper.git
cd facebook-helper
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m facebook_helper
```

Lần sau dùng `start.bat`. Trên macOS/Linux dùng `python3 -m venv .venv` rồi các lệnh tương tự với `.venv/bin/python`. Linux cần thư viện Qt/Chromium và desktop. Có thể dùng `--data-dir /duong/dan/rieng` để tách dữ liệu thử nghiệm.

## Bản 0.4.2: bỏ chặn đối chiếu nội dung

Đã bỏ hoàn toàn việc so sánh bản lưu với văn bản đọc từ Facebook, kể cả độ dài, từng chữ, số và kiểu định dạng trong DOM. Các test cũ yêu cầu chặn sai số tiền/thiếu đoạn do đối chiếu không còn là hành vi của bản này. Ứng dụng chỉ chờ chữ được nhận, ảnh tải xong và nút Đăng bấm được; nội dung/định dạng cuối cùng cần được người dùng kiểm tra trong Facebook.

Vẫn dừng khi ô trống, thiếu tệp ảnh, sai nhóm, Facebook báo lỗi/hạn chế/xác thực hoặc chưa rõ kết quả sau bấm. Không tự dán lại hoặc bấm Đăng lần hai khi kết quả chưa rõ. Tự đăng được bật mặc định; nhóm tiếp theo được thực hiện tự động khi bài trước gửi xong.

## Kiểm thử và đóng gói

[Thư viện và giấy phép](docs/THIRD-PARTY.md). Thư viện được đóng kèm, không cần CDN khi chạy.

Xem [kiểm thử bản 0.6.0](docs/TESTING-v0.6.0.md), [kiểm thử bản 0.5.0](docs/TESTING-v0.5.0.md), [kiểm thử bản 0.4.2](docs/TESTING-v0.4.2.md), [kiểm thử bản 0.4.1](docs/TESTING-v0.4.1.md), [kiểm thử bản 0.4](docs/TESTING-v0.4.md), [kiểm thử bản 0.3](docs/TESTING-v0.3.md), [kiểm thử bản 0.2](docs/TESTING-v0.2.md) và [kiểm thử bản 0.1](docs/TESTING.md). Test trình duyệt chạy Chromium với HTML mô phỏng, không đăng Facebook thật.

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
ruff check .
ruff format --check .
QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu pytest -q
```

Các biến Qt offscreen/sandbox trong lệnh trên chỉ dùng cho môi trường kiểm thử Linux dạng container; không thiết lập chúng để né kiểm tra của Facebook. Bản Windows dùng Qt native và sandbox mặc định.

Workflow **Build Windows** tạo gói portable, chạy file `.exe` với Qt và Chromium trên Windows, rồi chỉ phát hành khi kiểm tra thành công. Chạy thủ công ở Actions; trường `release_tag` cho phép phát hành phiên bản mới. Hướng dẫn từng gói nằm trong `HUONG-DAN.txt` đi kèm.
