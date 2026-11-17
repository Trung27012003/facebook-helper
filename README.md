# Facebook Helper · HR

Ứng dụng desktop tiếng Việt cho một người dùng: soạn tin tuyển dụng theo mẫu, chọn nhóm bằng nhãn và thực hiện danh sách đăng lần lượt. **Python + PySide6 + Playwright + SQLite**.

## Tải về và mở ứng dụng

**[Tải bản Windows 10/11 64-bit](https://github.com/Trung27012003/facebook-helper/releases/latest/download/FacebookHelper-Windows-x64.zip)** · [Các bản phát hành](https://github.com/Trung27012003/facebook-helper/releases)

Giải nén **toàn bộ** ZIP → mở thư mục `FacebookHelper` → nhấp đúp `FacebookHelper.exe`. Không cần cài Python hay Chromium. Giữ nguyên `_internal` đi kèm, không chạy bên trong ZIP. Bản portable chưa ký mã số; thông tin kiểm tra và SHA256 nằm ở trang phát hành.

## Cách dùng bản 0.7.1 · Summernote

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

### 3. Đăng bài qua bốn bước

Mở **Hướng dẫn nhanh** nếu cần: đăng nhập Facebook trong cửa sổ riêng của ứng dụng, thêm nhóm rồi soạn bài.

1. **Chọn bài:** trong Soạn bài bấm **Đăng bài này** để lưu và mở luồng đăng. Hoặc vào Đăng bài, chọn một bài đã lưu và xem nội dung.
2. **Chọn nơi đăng:** chọn một nhóm, tích nhiều nhóm hoặc chọn theo nhãn. Có thể bỏ tích những nhóm không cần. Số nhóm và thứ tự hiển thị là thứ tự sẽ thực hiện.
3. **Xem lại:** đọc nội dung, xem ảnh và danh sách nhóm. Chọn tự bấm Đăng hoặc chỉ chuẩn bị; có thể chỉnh thời gian giữa nhóm. Bấm **Bắt đầu đăng** là xác nhận gửi cho danh sách vừa xem. Nếu bài/nhóm thay đổi sau khi xem lại, phải quay lại xem trước khi bắt đầu. Facebook có thể đổi định dạng so với bản xem trước.
4. **Đăng và xem kết quả:** theo dõi nhóm đang làm, thao tác và tiến độ. Có thể **Tạm dừng**; thao tác đang chạy sẽ hoàn tất. Nút Quay lại/Tiếp tục được đặt dưới vùng cuộn. **Tùy chọn khác: xử lý bằng tay** chứa điền bài, đăng bản đang mở, báo đã gửi và bỏ qua nhóm.

**Lưu đợt đăng để chạy sau** chỉ lưu danh sách, không gửi Facebook. Có thể chuẩn bị nhiều đợt cho nhiều bài, rồi mở đợt đã lưu để Bắt đầu / tiếp tục. Mỗi lượt giữ nội dung và ảnh tại thời điểm tạo. Việc tiếp tục đợt đã lưu có xác nhận riêng trước khi gửi.

Sau mỗi bài, hệ thống tự cập nhật kết quả gửi và chuyển nhóm sau thời gian chờ. Không cần xác nhận giữa các nhóm; chờ duyệt không làm dừng danh sách. Lỗi hoặc chưa rõ kết quả sẽ dừng để tránh trùng. **Chỉ chuẩn bị bài** sẽ điền bài nhưng không bấm Đăng; công cụ xử lý bằng tay tự hiện để bạn báo kết quả rồi sang nhóm sau.

Bản 0.7.1 sửa lỗi khôi phục nháp khi mã bài bị dùng lại, tìm kiếm quá 250 ký tự, Hoàn tác khi nạp bài và nhận diện link chỉ trùng tiêu đề. Nháp cũ thiếu định danh được khôi phục thành bài mới để giữ bài đã lưu.

### Bản nháp tự lưu

Nội dung đang soạn được tự lưu riêng sau khi ngừng nhập khoảng 1,2 giây và trước khi đóng ứng dụng. Nháp giữ tên, HTML, hashtag và thứ tự ảnh; **không tự đưa vào danh sách bài có thể đăng**, không cập nhật bài đã lưu hay lượt đã tạo.

Mở lại ứng dụng → Soạn bài → **Khôi phục bản nháp**. Có nhiều nháp thì chọn theo tên và thời gian. Nếu bài gốc đã bị xóa, nháp được mở như bài mới. Không tự bỏ các nháp cũ khi bạn bắt đầu một bài mới; nút Bỏ các bản nháp cũ có xác nhận riêng. Khi bấm Lưu bài thành công, nháp tương ứng được xóa. Khi cố ý bỏ chỉnh sửa để chuyển bài, nháp của phần chỉnh sửa đó cũng được bỏ.

Nếu không tự lưu được khi đóng, ứng dụng giữ cửa sổ mở và báo để bạn lưu hoặc kiểm tra ổ đĩa. Thay đổi trong khoảng ngay trước sự cố mất điện có thể chưa kịp được lưu. Nháp nằm trong SQLite và được đưa vào bản sao lưu dữ liệu; ảnh dùng các tệp đã nhập vào ứng dụng.

### Quản lý bài đăng

Tab **Bài đã đăng** có tổng quan hôm nay, số lượt còn lại/chờ duyệt/cần xử lý. Tìm từ khóa trong tiêu đề, nội dung, nhóm, ghi chú hoặc link; lọc theo bài, nhóm, nhãn nhóm, trạng thái. Chọn ngày tạo lượt, **ngày gửi thực tế** hoặc ngày kiểm tra để lọc khoảng ngày (giờ trên máy, gồm cả hai đầu). Ngày gửi được ghi khi ứng dụng gửi thành công hoặc bạn bấm xác nhận vừa gửi; chỉ sửa trạng thái không tự tạo ngày gửi. Lượt cũ chưa ghi ngày gửi sẽ không xuất hiện khi lọc ngày gửi; không lấy ngày tạo thay thế.

Tích ô trước một/nhiều dòng hoặc **Chọn tất cả kết quả đang hiện** → **Kiểm tra bài đã chọn**, hoặc kiểm tra toàn bộ kết quả đang lọc. Bảng chính chỉ có năm cột: ô chọn, bài, nhóm, kết quả và thời gian gửi; không phải kéo ngang để tìm link. Bấm vào dòng rồi **Xem chi tiết** để đọc link, ghi chú, thời gian kiểm tra và lịch sử. Các nút **Hôm nay / 7 ngày qua / Chờ duyệt / Cần xử lý** giúp lọc nhanh; bộ lọc đầy đủ và kiểm tra định kỳ nằm trong **Lọc thêm và cài đặt kiểm tra**. Có thể dừng kiểm tra, mở bài, sao chép link và xuất Excel theo ô đã tích hoặc bộ lọc. Lịch sử ghi nguồn thay đổi, thời điểm, trạng thái cũ/mới và bằng chứng đọc được.

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

![Xem lại bài và nhóm trước khi bắt đầu](docs/images/review-v0.7.png)

![Bảng kết quả gọn, tích chọn nhiều bài](docs/images/manager-v0.7.png)

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

[Kết quả chạy ngày 17/11/2026](docs/TEST-RUN-2026-11-17.md) · [Excel kết quả từng ca](docs/TEST-RESULTS-2026-11-17.xlsx).

[Checklist kiểm thử toàn bộ](docs/TEST-CHECKLIST.md) và [bản Excel để đánh dấu](docs/TEST-CHECKLIST.xlsx) gồm đầu mục, ưu tiên, kết quả mong đợi và mẫu ghi lỗi.

[Kết quả chạy ngày 17/11/2026](docs/TEST-RUN-2026-11-17.md) · [Excel kết quả từng ca](docs/TEST-RESULTS-2026-11-17.xlsx).

[Checklist kiểm thử toàn bộ](docs/TEST-CHECKLIST.md) và [bản Excel để đánh dấu](docs/TEST-CHECKLIST.xlsx) gồm đầu mục, ưu tiên, kết quả mong đợi và mẫu ghi lỗi.

Xem [kiểm thử bản 0.7.1](docs/TESTING-v0.7.1.md), [kiểm thử bản 0.7.0](docs/TESTING-v0.7.0.md), [kiểm thử bản 0.6.0](docs/TESTING-v0.6.0.md), [kiểm thử bản 0.5.0](docs/TESTING-v0.5.0.md), [kiểm thử bản 0.4.2](docs/TESTING-v0.4.2.md), [kiểm thử bản 0.4.1](docs/TESTING-v0.4.1.md), [kiểm thử bản 0.4](docs/TESTING-v0.4.md), [kiểm thử bản 0.3](docs/TESTING-v0.3.md), [kiểm thử bản 0.2](docs/TESTING-v0.2.md) và [kiểm thử bản 0.1](docs/TESTING.md). Test trình duyệt chạy Chromium với HTML mô phỏng, không đăng Facebook thật.

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
ruff check .
ruff format --check .
QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu pytest -q
```

Các biến Qt offscreen/sandbox trong lệnh trên chỉ dùng cho môi trường kiểm thử Linux dạng container; không thiết lập chúng để né kiểm tra của Facebook. Bản Windows dùng Qt native và sandbox mặc định.

Workflow **Build Windows** tạo gói portable, chạy file `.exe` với Qt và Chromium trên Windows, rồi chỉ phát hành khi kiểm tra thành công. Chạy thủ công ở Actions; trường `release_tag` cho phép phát hành phiên bản mới. Hướng dẫn từng gói nằm trong `HUONG-DAN.txt` đi kèm.
