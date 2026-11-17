# Kiểm thử 0.8.2

Ngày 17/11/2026 (giờ Việt Nam).

## Phạm vi

- Bài đã đăng mặc định Từ ngày = Đến ngày = hôm nay. Tự sang ngày mới nếu vẫn dùng mặc định; không thay khoảng ngày/từ khóa do người dùng tự chọn.
- Màn hình Đăng bài có nút theo trạng thái: Bắt đầu/Tiếp tục khi còn việc, Tạm dừng khi đang chạy, Bài đã đăng được làm nổi bật khi hoàn tất. Đợt hoàn tất không còn Bắt đầu, hướng dẫn cũ hoặc thanh bước/nút tạo đợt lớn ở cuối. Lượt đang gửi bình thường không bị tính thành lỗi.
- Link hiển thị trực tiếp trong bảng. Hàng Mở bài / Sao chép link có thêm Mở nhóm ở cả hai trang. Thiếu link vẫn mở được nhóm; không có dòng được chọn thì tắt nút. Mở nhóm dùng trình duyệt mặc định, không điều hướng cửa sổ đang tự đăng.
- Nút Bài đã đăng từ một đợt sẽ mở đúng đợt, xóa từ khóa cũ và chọn khoảng ngày của các bản ghi trong đợt.

## Lấy link

Bản trước còn lọc request theo nội dung gửi đi khớp toàn bộ bản lưu. Tái hiện bằng mô phỏng: thay đổi văn bản trong request hoặc sửa bản đang mở làm bỏ qua phản hồi có mã bài hợp lệ. Bản mới gắn phản hồi với request tạo bài bắt đầu trong chính thao tác Đăng và đúng nhóm, không so nội dung với bản lưu. Phản hồi của request bắt đầu trước thao tác này bị bỏ qua.

Đã thêm chờ request bắt đầu muộn trong khoảng tối đa 3 giây sau khoảng chờ sau gửi; trước đó chỉ chờ khi đã thấy request đang tải. Mô phỏng request khởi chạy sau 1,8 giây đã được thêm vào test trình duyệt. Hỗ trợ các khung phản hồi GraphQL bổ sung có đường dẫn story_create/story đã nhận diện; không quét mọi ID hoặc tự gọi API riêng.

Nếu vẫn không lấy được link, file `link-diagnostics.json` trong dữ liệu giữ tối đa 30 lượt với phiên bản, thời gian, mã lượt cục bộ, số request/phản hồi và cờ hiện diện các trường mã bài. Kiểm thử xác nhận file không chứa nội dung, URL, mã Facebook, cookie/token hoặc phản hồi thô. Đây là chẩn đoán cục bộ, không tự gửi ra ngoài.

## Kiểm tra

| Nhóm | Các trường hợp |
|---|---|
| Ngày | Mặc định hôm nay, loại hôm qua, tự sang ngày mới, giữ bộ lọc tự chọn |
| Trạng thái UI | Chưa chạy, đang chạy, tạm dừng, hoàn tất; trạng thái nút/điểm nhấn; ẩn chỉ dẫn cũ; link có mặt trong bảng |
| Mở nhóm | Đúng dòng chọn, không cần link bài, tắt khi hết kết quả, không dùng worker đang đăng |
| Link | Nội dung request thay đổi; URL/mã bài; nhóm số/tên; request bắt đầu muộn; khung GraphQL bổ sung; không nhận phản hồi của request cũ |
| Dữ liệu chẩn đoán | Không lộ dữ liệu request/response, giới hạn 30 lượt |
| Hồi quy | Soạn thảo, nháp, ảnh, dữ liệu cũ, xóa cục bộ, cảnh báo trùng, tự chuyển nhóm, sao lưu, Excel và đóng gói |

Ảnh Qt offscreen dùng dữ liệu giả ở 980×680 và 1280×850: [Chưa chạy](qa/v0.8.2/posting-ready-980.png), [Đang chạy](qa/v0.8.2/posting-running-980.png), [Hoàn tất](qa/v0.8.2/posting-complete-980.png), [Lọc hôm nay](qa/v0.8.2/today-980.png).

## Kết quả tại workspace

Ruff đạt. Lượt chạy toàn bộ đầu tiên: 289 đạt, 1 kỳ vọng giao diện cũ không còn phù hợp (bật lại mọi nút sau lỗi, kể cả Bắt đầu khi chưa chọn đợt). Đã cập nhật ca đó để giữ kiểm tra chặn thao tác đồng thời và xác nhận Bắt đầu vẫn tắt khi chưa có đợt. Sau các thay đổi cuối và bổ sung Mở nhóm, **77 ca liên quan đạt**, kiểm tra khởi động/Chromium/Qt riêng **1 ca đạt**. Toàn bộ hiện có 292 test; kết quả CI trên commit phát hành ghi bên dưới.

## Giới hạn

Không có phiên Facebook thật hoặc phản hồi của tài khoản người dùng để xác định chính xác nguyên nhân thực tế. Các nguyên nhân lọc nội dung và request muộn được tái hiện bằng mô phỏng; không khẳng định đã bao phủ mọi cấu trúc Facebook. Không có URL/mã bài hợp lệ được nhận diện thì chưa lấy được link; link chờ duyệt vẫn có thể chưa mở được. Ảnh Qt offscreen không thay nghiệm thu DPI Windows.
