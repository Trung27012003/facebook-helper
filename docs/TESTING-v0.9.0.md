# Kiểm thử 0.9.0 — giao diện toàn ứng dụng

Ngày 17/11/2026 (giờ Việt Nam). Bản này gồm phần lọc hôm nay, mở nhóm, lấy link và bố cục đăng bài đã chuẩn bị cho 0.8.2; gói Windows 0.8.2 không phát hành. Schema dữ liệu vẫn là 6.

## Phạm vi

| Màn hình | Hành vi cuối |
|---|---|
| Soạn bài | Thư viện bên trái, nội dung bên phải. Bài mới/Từ mẫu rõ ràng; thao tác phụ và ảnh gom menu. Lưu là nút chính khi sửa; Chọn nhóm đăng là nút chính sau khi lưu. Đi thẳng đến chọn nhóm, vẫn phải xem lại trước khi gửi. Nút chính cố định ngoài vùng cuộn |
| Nhóm | Thư viện và biểu mẫu tách biệt. Kiểm tra link ngay khi nhập, chỉ bật Lưu khi hợp lệ và có thay đổi. Xóa nằm trong menu, giữ rõ dòng đang mở, mở nhóm bằng trình duyệt mặc định |
| Đăng bài | Nút theo trạng thái; hoàn tất ẩn Bắt đầu/hướng dẫn cũ, làm nổi bật Bài đã đăng. Hiện link và Mở bài/Sao chép/Mở nhóm. Không bật thao tác điều hướng worker trong lúc tự đăng |
| Bài đã đăng | Mặc định hôm nay, giữ bộ lọc tự chọn. Tìm kiếm là hành động chính; nhóm nút mở/copy tách khỏi xuất/xóa. Xóa có màu riêng |
| Cài đặt | Ba phần Tài khoản/Dữ liệu/Hỗ trợ; Đăng nhập là nút chính, có sao lưu và xuất chẩn đoán riêng |
| Mẫu tuyển dụng | Gom trường thành Thông tin/Nội dung/Liên hệ; Tạo bài nổi bật và chỉ bật khi đủ vị trí/công ty |

Nền sáng, thẻ trắng, tab đang chọn dùng nền xanh nhạt để phân biệt với nút hành động xanh đậm. Hướng dẫn dài chuyển khỏi màn hình thao tác thường ngày; trợ giúp vẫn mở khi cần. Không thay Summernote bằng toolbar tự viết.

## Các ca mới

- Lưu → nút Chọn nhóm đăng nổi bật; sửa lại → Lưu nổi bật. Bấm chọn nhóm không gửi bài hoặc tạo đợt trước bước xem lại.
- Cập nhật trạng thái nút không gọi JavaScript hoặc chờ WebEngine, dùng cache tài liệu.
- Chỉ dẫn bài đã lưu/nháp không mâu thuẫn với nút chính; chọn nhóm đăng tắt trong lúc có đợt đang chạy, vẫn cho lưu nháp.
- Menu ảnh sắp xếp đúng tệp và thứ tự. Với ảnh đính kèm, cửa sổ vẫn đúng 980×680, các nút lưu/tiếp tục nằm trong cửa sổ.
- Biểu mẫu nhóm không lưu link ngoài Facebook, bật Lưu khi hợp lệ, tắt khi đã lưu, nút Mở nhóm đúng URL.
- Xuất chẩn đoán chỉ chép file metadata cục bộ, không dùng worker hoặc xuất DB/phiên đăng nhập.
- Mẫu chỉ bật Tạo bài khi đủ hai trường bắt buộc.

Các ca lấy link kế thừa gồm: không so toàn bộ nội dung request với bản lưu, không nhận phản hồi của request bắt đầu trước thao tác Đăng, chờ request khởi chạy sau 1,8 giây, URL/mã bài/khung GraphQL bổ sung, sai nhóm/mã mâu thuẫn và bảo vệ dữ liệu chẩn đoán. Xem [phạm vi nền 0.8.2](TESTING-v0.8.2.md).

## Ảnh giao diện

Dữ liệu giả, chụp Qt offscreen ở 980×680 và 1280×850:

- [Soạn bài](qa/v0.9.0/editor-980.png)
- [Nhóm](qa/v0.9.0/groups-980.png)
- [Đăng bài: chưa chạy](qa/v0.9.0/posting-ready-980.png), [đang chạy](qa/v0.9.0/posting-running-980.png), [hoàn tất](qa/v0.9.0/posting-complete-980.png)
- [Bài đã đăng](qa/v0.9.0/today-980.png)
- [Cài đặt](qa/v0.9.0/settings-980.png)

## Kiểm tra tại workspace

Ruff và kiểm tra diff đạt. Các lượt kiểm tra liên quan sau thay đổi gồm 66 ca UI/luồng, 25 ca soạn/nháp/mẫu/khởi động, 44 ca luồng/UI, và 9 ca UX/mẫu/khởi động đều đạt. Các tập này có giao nhau; không cộng thành tổng. Bộ kiểm thử hiện có 298 ca; kết quả chạy toàn bộ trên CI của commit phát hành ghi bên dưới.

## Giới hạn

Chưa có phiên Facebook thật hoặc phản hồi từ tài khoản người dùng để chứng minh lỗi lấy link thực tế đã hết. Không có URL/mã bài hợp lệ được nhận diện thì chưa lấy được link, link chờ duyệt có thể chưa mở được. File chẩn đoán cục bộ giúp xác định tiếp nếu còn lỗi. Kiểm thử Chromium dùng trang/phản hồi mô phỏng. Ảnh Qt offscreen không thay nghiệm thu DPI Windows hoặc thử nghiệm với người dùng mới; kiểm tra `.exe` Windows là kiểm tra khởi động, không phải chứng minh Facebook thật hoạt động.

## CI mã nguồn

[Checks #44119114421](https://github.com/Trung27012003/facebook-helper/actions/runs/44119114421) đạt trên commit `7b3277d5591d7c4037572da0a57d941e9ae467fb`: Ruff và **298 test, 214,241 giây**, 0 failures/errors/skipped. [JUnit CI](qa/v0.9.0/ci-tests.xml).

## Windows và tải về

[Build Windows #44119114541](https://github.com/Trung27012003/facebook-helper/actions/runs/44119114541) đạt trên cùng commit. `.exe` chạy trong thư mục có dấu/khoảng trắng, kiểm tra Qt, Chromium, Summernote/dán-copy HTML, bốn bước, bộ lọc hôm nay, cột link, Mở nhóm, các action mới, nháp và đóng worker. ZIP gồm 4.000 tệp; rà tên tệp không thấy dữ liệu/phiên người dùng thuộc danh sách cấm. [Bằng chứng](qa/v0.9.0/windows-verification.json).

[Tải bản 0.9.0](https://github.com/Trung27012003/facebook-helper/releases/tag/v0.9.0). ZIP 620.992.045 byte; SHA256 công bố `f4749433edf0050cac74ccdd25da9c75480c43db21a2256f168ef3073ba07619`. Đã tải checksum và kiểm tra đầu ZIP từ link công khai: HTTP 206, chữ ký `504b0304`. Không tải toàn bộ ZIP để tính lại hash tại workspace.
