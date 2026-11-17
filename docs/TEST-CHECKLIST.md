# Checklist kiểm thử toàn bộ Facebook Helper

Áp dụng cho bản **0.7.0** và dùng làm danh sách hồi quy cho các bản sau. Ngày lập: **17/11/2026 (giờ Việt Nam)**.

Đây là kế hoạch kiểm thử, mọi ca bên dưới bắt đầu ở **Chưa chạy**. Không ánh xạ một-một các ca này với số lượng test tự động. Bằng chứng đã chạy của bản 0.7.0 nằm tại [báo cáo 180 test](TESTING-v0.7.0.md); các test Facebook trong đó dùng mô phỏng. Các ca tích hợp Facebook và nghiệm thu người dùng cần ghi kết quả riêng trên bản chạy thực tế.

[Tải bản Excel để đánh dấu kết quả](TEST-CHECKLIST.xlsx) · Excel có bộ lọc, danh sách chọn trạng thái, ô ghi chú và trang tổng hợp.

## Chuẩn bị và cách đánh dấu

- Dùng bản sao dữ liệu hoặc thư mục dữ liệu thử; giữ bản sao lưu trước khi thử lỗi, cập nhật và khôi phục.
- Chuẩn bị hai bài có nội dung/ảnh khác nhau; một bài dài có chữ Việt, định dạng và hashtag; ít nhất ba nhóm thử đã được phép đăng, có nhãn chung và nhãn riêng. Có nhóm yêu cầu duyệt và trường hợp thiếu quyền xem/đăng để kiểm tra lỗi.
- Thử đăng thật trong nhóm thử của bạn hoặc nơi đã có sự đồng ý. Các ca hết dung lượng, lỗi DB, ngắt tiến trình và chạy lâu dành cho kỹ thuật, thực hiện bằng giả lập/bản sao.
- Đổi ô Kết quả thành **Đạt / Không đạt / Bị chặn / Không áp dụng** sau khi thực hiện. Ca bị chặn cần lý do; không đánh Đạt chỉ vì chưa thấy lỗi.
- Khi có lỗi, ghi mã ca, phiên bản, Windows/DPI, bước tái hiện, kết quả thực tế và ảnh/log đã loại thông tin đăng nhập. Không đưa mật khẩu/cookie vào báo cáo.

**Ưu tiên:** P0 = nguy cơ mất dữ liệu, gửi sai/trùng hoặc báo sai kết quả quan trọng; P1 = luồng sử dụng chính và khôi phục lỗi; P2 = độ tiện dụng, hiển thị và hiệu năng. Đây là mức ưu tiên kiểm thử, không phải mức độ lỗi đã được phát hiện.

## Danh mục

1. [Cài đặt, mở và đóng ứng dụng](#kt-01)
2. [Hướng dẫn lần đầu và điều hướng](#kt-02)
3. [Đăng nhập và phiên Facebook](#kt-03)
4. [Tạo và quản lý bài viết](#kt-04)
5. [Soạn thảo và dán giữ định dạng](#kt-05)
6. [Mẫu tuyển dụng, hashtag và xem trước](#kt-06)
7. [Ảnh đính kèm](#kt-07)
8. [Tự lưu và khôi phục nháp](#kt-08)
9. [Khai báo và quản lý nhóm](#kt-09)
10. [Nhãn và chọn nơi đăng](#kt-10)
11. [Luồng đăng bài bốn bước](#kt-11)
12. [Nhiều bài và nhiều đợt đăng](#kt-12)
13. [Tự đăng lên Facebook](#kt-13)
14. [Đăng thủ công và công cụ hỗ trợ](#kt-14)
15. [Tạm dừng, sự cố và tiếp tục](#kt-15)
16. [Chống đăng trùng](#kt-16)
17. [Theo dõi trạng thái và duyệt bài](#kt-17)
18. [Bảng kết quả, tìm kiếm và bộ lọc](#kt-18)
19. [Link bài và ảnh minh chứng](#kt-19)
20. [Lịch sử, thời gian và tính toàn vẹn trạng thái](#kt-20)
21. [Xuất Excel, sao lưu và khôi phục](#kt-21)
22. [Cập nhật, bảo vệ dữ liệu và quyền riêng tư](#kt-22)
23. [Khả dụng với người mới và hiển thị](#kt-23)
24. [Hiệu năng và chạy lâu — dành cho kỹ thuật](#kt-24)
25. [Nghiệm thu công việc hằng ngày](#kt-25)

<a id="kt-01"></a>

## 01. Cài đặt, mở và đóng ứng dụng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-01-01 | P0 | Mở ZIP đã giải nén trên máy Windows chưa cài Python | Ứng dụng mở được, có trình soạn và Chromium đi kèm. | Chưa chạy |
| KT-01-02 | P1 | Mở từ thư mục có dấu tiếng Việt và khoảng trắng | Đọc tài nguyên, ảnh và dữ liệu đúng; không lỗi đường dẫn. | Chưa chạy |
| KT-01-03 | P0 | Mở hai phiên ứng dụng dùng cùng dữ liệu | Phiên thứ hai bị chặn; phiên đang chạy không bị đổi trạng thái gửi. | Chưa chạy |
| KT-01-04 | P1 | Đóng khi không có công việc đang chạy | Đóng sạch, không để tiến trình trình duyệt của ứng dụng chạy mãi. | Chưa chạy |
| KT-01-05 | P0 | Đóng khi đang gửi bài | Thao tác đang chạy được xử lý theo luồng đóng; không tự chuyển nhóm tiếp. Mở lại không tự gửi lại lượt chưa rõ. | Chưa chạy |
| KT-01-06 | P1 | Thiếu thư mục tài nguyên hoặc Chromium trong bản giải nén thử | Có thông báo để giải nén lại/khắc phục; không báo giả đã gửi. | Chưa chạy |

<a id="kt-02"></a>

## 02. Hướng dẫn lần đầu và điều hướng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-02-01 | P1 | Mở với thư mục dữ liệu mới | Hiện hướng dẫn đăng nhập → thêm nhóm → soạn bài. | Chưa chạy |
| KT-02-02 | P1 | Bấm từng nút trong hướng dẫn | Mở đúng cửa sổ Facebook hoặc đúng tab ứng dụng. | Chưa chạy |
| KT-02-03 | P2 | Ẩn hướng dẫn rồi mở lại ứng dụng | Ghi nhớ lựa chọn ẩn; không bật hướng dẫn lặp lại. | Chưa chạy |
| KT-02-04 | P2 | Mở lại Hướng dẫn nhanh | Hiện lại hướng dẫn mà không làm mất bài đang soạn. | Chưa chạy |
| KT-02-05 | P1 | Chuyển giữa năm tab khi có dữ liệu | Mở đúng chức năng, không tự gửi bài hoặc mất nội dung. | Chưa chạy |
| KT-02-06 | P1 | Bấm Tiếp tục danh sách còn lại | Mở đợt còn việc; chỉ gửi sau khi người dùng bắt đầu. | Chưa chạy |

<a id="kt-03"></a>

## 03. Đăng nhập và phiên Facebook

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-03-01 | P1 | Đăng nhập tài khoản thử trong trình duyệt ứng dụng | Người dùng đăng nhập trực tiếp với Facebook, không nhập mật khẩu vào phần mềm. | Chưa chạy |
| KT-03-02 | P1 | Đăng nhập với xác thực hai bước | Chờ người dùng hoàn tất; không tự vượt bước xác thực. | Chưa chạy |
| KT-03-03 | P1 | Đóng/mở lại sau khi đăng nhập thành công | Phiên được dùng lại nếu Facebook còn chấp nhận. | Chưa chạy |
| KT-03-04 | P0 | Phiên hết hạn hoặc Facebook chuyển về trang đăng nhập | Dừng thao tác, có hướng dẫn; không ghi đã đăng thành công. | Chưa chạy |
| KT-03-05 | P1 | Đăng xuất trong Facebook rồi gửi/kiểm tra bài | Phát hiện cần đăng nhập hoặc giữ kết quả chưa xác minh; không tiếp tục gửi mù. | Chưa chạy |
| KT-03-06 | P1 | Đóng cửa sổ trình duyệt rồi mở lại từ ứng dụng | Có thể tạo lại cửa sổ và tiếp tục thao tác phù hợp. | Chưa chạy |
| KT-03-07 | P1 | Dùng Chrome cá nhân song song | Không nhầm phiên trình duyệt cá nhân với phiên của ứng dụng. | Chưa chạy |

<a id="kt-04"></a>

## 04. Tạo và quản lý bài viết

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-04-01 | P1 | Tạo bài mới, lưu và mở lại | Đúng tên, nội dung, hashtag và ảnh. | Chưa chạy |
| KT-04-02 | P1 | Thiếu tên bài hoặc nội dung khi Lưu bài | Có hướng dẫn bổ sung, không tạo bài không hợp lệ. | Chưa chạy |
| KT-04-03 | P1 | Sửa một bài đã lưu | Chỉ cập nhật bài được chọn, không đổi bài khác. | Chưa chạy |
| KT-04-04 | P1 | Nhân bản bài rồi chỉnh sửa | Tạo bản riêng; bài gốc và lịch sử vẫn giữ. | Chưa chạy |
| KT-04-05 | P1 | Tìm bài theo tên và nội dung | Danh sách hiển thị đúng các bài khớp phạm vi tìm kiếm. | Chưa chạy |
| KT-04-06 | P0 | Chuyển bài khi đang có sửa chưa lưu: đồng ý/từ chối bỏ sửa | Từ chối giữ nguyên nội dung; đồng ý mới bỏ phần sửa và nháp tương ứng. | Chưa chạy |
| KT-04-07 | P1 | Xóa bài đã lưu | Có xác nhận; lịch sử các lượt đã tạo vẫn còn. | Chưa chạy |

<a id="kt-05"></a>

## 05. Soạn thảo và dán giữ định dạng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-05-01 | P1 | Chữ Việt, xuống dòng, đoạn văn và emoji | Lưu/mở/copy không mất chữ hoặc hỏng dấu. | Chưa chạy |
| KT-05-02 | P1 | Đậm, nghiêng, gạch chân, tiêu đề và danh sách | Trình soạn, lưu lại và bản xem trước giữ các định dạng được hỗ trợ. | Chưa chạy |
| KT-05-03 | P1 | Font, cỡ, màu chữ, bảng và liên kết | Điều khiển của Summernote hoạt động; lưu/mở không lỗi editor. | Chưa chạy |
| KT-05-04 | P1 | Dán bài từ Word | Giữ phần định dạng được hỗ trợ; không dán thành mã HTML thô. | Chưa chạy |
| KT-05-05 | P1 | Dán bài từ Facebook nền tối | Bỏ nền tối/màu giao diện gây khó đọc, giữ nội dung và cấu trúc phù hợp. | Chưa chạy |
| KT-05-06 | P1 | Dán chữ thuần và xóa định dạng | Cho ra chữ đọc được; không sót nền/mã thừa. | Chưa chạy |
| KT-05-07 | P1 | Hoàn tác/làm lại sau sửa hoặc dán | Trở về đúng trạng thái trong phiên soạn. | Chưa chạy |
| KT-05-08 | P0 | Dán HTML có script hoặc tài nguyên ngoài không phù hợp | Nội dung được làm sạch; không chạy script tùy ý hoặc tự tải ảnh như tệp đính kèm. | Chưa chạy |
| KT-05-09 | P1 | Bài dài trên 15.000 ký tự và nhiều đoạn | Không chặn vì so khớp số ký tự đọc lại; vẫn cần chữ, ảnh và nút gửi sẵn sàng. | Chưa chạy |

<a id="kt-06"></a>

## 06. Mẫu tuyển dụng, hashtag và xem trước

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-06-01 | P1 | Tạo bài từ mẫu tuyển dụng đủ thông tin | Sinh đúng vị trí, công ty, việc làm, yêu cầu, quyền lợi và liên hệ. | Chưa chạy |
| KT-06-02 | P1 | Bỏ trống trường không bắt buộc của mẫu | Không sinh đoạn lỗi hoặc giá trị rỗng khó hiểu. | Chưa chạy |
| KT-06-03 | P0 | Hủy tạo mẫu khi đang soạn bài khác | Không ghi đè bài đang soạn khi chưa được đồng ý. | Chưa chạy |
| KT-06-04 | P1 | Sửa nội dung sau khi sinh từ mẫu | Bài vẫn chỉnh sửa và lưu bình thường. | Chưa chạy |
| KT-06-05 | P1 | Thêm hashtag cuối bài | Lưu, xem trước, copy và lượt đăng có hashtag đúng vị trí. | Chưa chạy |
| KT-06-06 | P1 | Xem trước bài có ảnh/định dạng | Hiển thị đúng dữ liệu đã chọn; không cam kết Facebook giữ mọi màu/font như Word. | Chưa chạy |

<a id="kt-07"></a>

## 07. Ảnh đính kèm

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-07-01 | P1 | Nhập một ảnh và nhiều ảnh hợp lệ | Có ảnh trong danh sách và bản sao thuộc dữ liệu ứng dụng. | Chưa chạy |
| KT-07-02 | P1 | Ảnh ở đường dẫn có dấu/khoảng trắng | Nhập, mở, xem trước và tải lên được. | Chưa chạy |
| KT-07-03 | P1 | Đưa ảnh lên/xuống, bỏ ảnh và thêm lại | Thứ tự, nhãn Ảnh 1/2/3 và số ảnh nhất quán. | Chưa chạy |
| KT-07-04 | P0 | Xóa hoặc di chuyển tệp ảnh nguồn sau khi nhập | Bản sao đã nhập vẫn dùng được; không phụ thuộc tệp nguồn. | Chưa chạy |
| KT-07-05 | P1 | Chọn tệp hỏng, không phải ảnh hoặc trên 30 MB | Báo đúng lỗi; các ảnh hợp lệ đã nhập không bị mất. | Chưa chạy |
| KT-07-06 | P0 | Tệp ảnh trong dữ liệu bị thiếu trước khi gửi | Dừng trước khi gửi thiếu ảnh; giữ công việc để khắc phục. | Chưa chạy |
| KT-07-07 | P1 | Ảnh có trong nội dung copy từ Word/Facebook | Không nhầm ảnh dán trong HTML với ảnh đã nhập để đính kèm. | Chưa chạy |

<a id="kt-08"></a>

## 08. Tự lưu và khôi phục nháp

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-08-01 | P0 | Nhập rồi ngừng khoảng 1,2 giây | Lưu nháp riêng; không tự đưa nháp vào thư viện hoặc gửi Facebook. | Chưa chạy |
| KT-08-02 | P0 | Nháp của một bài đã lưu | Tự lưu không ghi đè bài đã lưu hoặc các lượt đã tạo. | Chưa chạy |
| KT-08-03 | P0 | Đóng/mở lại rồi khôi phục | Khôi phục tên, chữ Việt, HTML, hashtag, ảnh và thứ tự. | Chưa chạy |
| KT-08-04 | P0 | Bắt đầu nháp khác khi còn nháp cũ chưa khôi phục | Không ghi mất các nháp cũ. | Chưa chạy |
| KT-08-05 | P1 | Có nhiều nháp cần khôi phục | Chọn được theo tên/thời gian; mở đúng nháp. | Chưa chạy |
| KT-08-06 | P0 | Bấm Lưu bài thành công | Cập nhật đúng bài và dọn nháp tương ứng; giữ các nháp khác. | Chưa chạy |
| KT-08-07 | P0 | Không ghi được nháp khi đóng, giả lập trên dữ liệu thử | Giữ cửa sổ mở và báo lỗi để tránh bỏ mất nội dung. | Chưa chạy |
| KT-08-08 | P0 | Khôi phục nháp thiếu tệp ảnh | Không thay bài hiện tại hoặc tự xóa nháp; có thông báo. | Chưa chạy |
| KT-08-09 | P1 | Bài gốc của nháp đã bị xóa | Mở nháp như bài mới, không ghi nhầm bài khác. | Chưa chạy |
| KT-08-10 | P1 | Bỏ các nháp cũ: đồng ý/từ chối | Chỉ xóa sau xác nhận; không xóa bài đã lưu hoặc nháp hiện đang sửa. | Chưa chạy |

<a id="kt-09"></a>

## 09. Khai báo và quản lý nhóm

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-09-01 | P1 | Thêm nhóm với tên và link hợp lệ | Lưu và xuất hiện trong các màn chọn nhóm. | Chưa chạy |
| KT-09-02 | P1 | Sửa tên, link và ghi chú nhóm | Đúng nhóm; không ghi đè nhóm khác. | Chưa chạy |
| KT-09-03 | P0 | Link sai miền, HTTP, trang Facebook không phải nhóm | Từ chối link không hợp lệ hoặc không xác định được nhóm. | Chưa chạy |
| KT-09-04 | P1 | Các biến thể www/m/web và tham số chia sẻ hợp lệ | Chuẩn hóa đúng nhóm được hỗ trợ; không tạo bản trùng chỉ vì biến thể miền. | Chưa chạy |
| KT-09-05 | P1 | Thêm lại cùng link nhóm đã có | Cảnh báo trùng; không tạo thêm nhóm giống hệt. | Chưa chạy |
| KT-09-06 | P1 | Chuyển nhóm khi có sửa chưa lưu | Chỉ bỏ sửa khi người dùng đồng ý. | Chưa chạy |
| KT-09-07 | P1 | Xóa nhóm đã có lịch sử | Có xác nhận; lịch sử và thông tin chụp tại lúc tạo lượt vẫn còn. | Chưa chạy |

<a id="kt-10"></a>

## 10. Nhãn và chọn nơi đăng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-10-01 | P1 | Nhiều nhóm chung một nhãn | Chọn nhãn hiển thị đúng tất cả nhóm thuộc nhãn. | Chưa chạy |
| KT-10-02 | P1 | Một nhóm có nhiều nhãn | Nhóm xuất hiện ở từng nhãn phù hợp, không nhân đôi trong một đợt. | Chưa chạy |
| KT-10-03 | P1 | Nhãn khác hoa/thường, dấu #, dấu phân cách | Chuẩn hóa theo quy tắc; không coi Hà Nội mở rộng là nhãn Hà Nội. | Chưa chạy |
| KT-10-04 | P1 | Chọn một nhóm và chọn nhiều nhóm bằng ô tích | Đếm đúng nhóm và giữ thứ tự hiển thị. | Chưa chạy |
| KT-10-05 | P0 | Chọn theo nhãn rồi bỏ tích vài nhóm | Chỉ nhóm còn tích được đưa vào đợt đăng. | Chưa chạy |
| KT-10-06 | P1 | Không có nhãn/nhóm phù hợp | Hiện trạng thái rỗng và cách thêm dữ liệu, không tạo đợt rỗng. | Chưa chạy |

<a id="kt-11"></a>

## 11. Luồng đăng bài bốn bước

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-11-01 | P1 | Đăng bài này từ trình soạn | Lưu bài hợp lệ và mở đúng bài ở bước Chọn bài; chưa gửi Facebook. | Chưa chạy |
| KT-11-02 | P1 | Đi lần lượt Chọn bài → nơi đăng → xem lại | Mỗi bước có nội dung/nút phù hợp; chưa tạo/gửi trước thao tác cuối. | Chưa chạy |
| KT-11-03 | P0 | Xem lại nội dung, số ảnh, ảnh và toàn bộ nhóm | Các thông tin khớp với dữ liệu chuẩn bị gửi. | Chưa chạy |
| KT-11-04 | P0 | Sửa bài, ảnh hoặc nhóm sau khi đã xem lại | Yêu cầu xem lại trước khi bắt đầu; không gửi bản không được xem lại. | Chưa chạy |
| KT-11-05 | P0 | Bắt đầu tự đăng từ bước xem lại | Tạo đúng một đợt và gửi nhóm đầu đúng một lần. | Chưa chạy |
| KT-11-06 | P0 | Lưu đợt đăng để chạy sau | Chỉ lưu công việc, không mở luồng gửi hoặc tự bấm Đăng. | Chưa chạy |
| KT-11-07 | P1 | Quay lại và sửa bài được chọn trong luồng đăng | Mở đúng bài; tôn trọng lựa chọn giữ phần sửa chưa lưu. | Chưa chạy |
| KT-11-08 | P1 | Đang chạy mà quay lại thay bài/nhóm | Yêu cầu tạm dừng và chờ thao tác hoàn tất. | Chưa chạy |

<a id="kt-12"></a>

## 12. Nhiều bài và nhiều đợt đăng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-12-01 | P0 | Chuẩn bị ít nhất hai bài với ảnh/nội dung khác nhau | Mỗi đợt giữ đúng bài và ảnh của mình, không lẫn dữ liệu. | Chưa chạy |
| KT-12-02 | P1 | Lưu nhiều đợt trước khi bắt đầu | Có thể chọn và chạy từng đợt độc lập. | Chưa chạy |
| KT-12-03 | P0 | Sửa bài gốc sau khi tạo đợt | Lượt đã tạo giữ bản chụp nội dung/ảnh cũ, không âm thầm đổi theo bài gốc. | Chưa chạy |
| KT-12-04 | P1 | Chuyển đợt khi đang chờ nhóm tiếp | Dừng chuyển tự động của đợt cũ; không gửi nhầm đợt. | Chưa chạy |
| KT-12-05 | P1 | Xem Tất cả lượt và một đợt cụ thể | Bảng/tiến độ phản ánh đúng phạm vi đang chọn. | Chưa chạy |
| KT-12-06 | P0 | Tiếp tục đợt đã hoàn tất một phần | Bỏ qua lượt đã gửi/chờ duyệt/hiển thị; xử lý phần còn lại. | Chưa chạy |

<a id="kt-13"></a>

## 13. Tự đăng lên Facebook

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-13-01 | P0 | Gửi một bài một nhóm thử | Mở đúng nhóm, đúng ô Tạo bài; không điền nhầm ô bình luận. | Chưa chạy |
| KT-13-02 | P0 | Đăng lần lượt nhiều nhóm thử | Đúng nhóm, đúng thứ tự, mỗi lượt chỉ bấm gửi một lần. | Chưa chạy |
| KT-13-03 | P1 | Ảnh đang tải, nút Đăng chưa sẵn sàng | Chờ sẵn sàng hoặc dừng khi hết thời gian; không gửi thiếu ảnh sớm. | Chưa chạy |
| KT-13-04 | P0 | Ô Facebook không nhận được chữ | Không tự gửi bài trống và không dán lặp vô hạn. | Chưa chạy |
| KT-13-05 | P1 | Facebook đổi định dạng hoặc phần đọc lại có chữ giao diện | Không chặn bằng so khớp độ dài; đánh giá định dạng theo khả năng Facebook hỗ trợ. | Chưa chạy |
| KT-13-06 | P0 | Facebook báo chờ duyệt sau khi gửi | Ghi kết quả phù hợp và tiếp tục nhóm sau. | Chưa chạy |
| KT-13-07 | P0 | Nhóm không cho đăng, thiếu quyền hoặc Facebook hạn chế | Dừng và hướng dẫn kiểm tra; không cố vượt hạn chế. | Chưa chạy |
| KT-13-08 | P0 | Đã thử bấm Đăng nhưng kết quả không rõ | Ghi chưa rõ, dừng đợt; không tự gửi lại hoặc coi là đã hiển thị. | Chưa chạy |

<a id="kt-14"></a>

## 14. Đăng thủ công và công cụ hỗ trợ

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-14-01 | P0 | Tắt Tự bấm Đăng | Chỉ chuẩn bị nội dung/ảnh, không bấm gửi. | Chưa chạy |
| KT-14-02 | P1 | Chế độ chỉ chuẩn bị | Công cụ báo đã đăng/sang nhóm sau hiện để tiếp tục bằng tay. | Chưa chạy |
| KT-14-03 | P0 | Điền bài vào bản nháp đã có nội dung | Không âm thầm ghi đè hoặc dán lặp bản đang soạn. | Chưa chạy |
| KT-14-04 | P0 | Đăng bản đang mở | Có xác nhận, không dán lại chữ/thêm lại ảnh; chặn khi đang ở sai nhóm. | Chưa chạy |
| KT-14-05 | P1 | Sao chép bài và mở thư mục ảnh | Đúng nội dung và ảnh của lượt đang chọn, đúng thứ tự xuất tệp. | Chưa chạy |
| KT-14-06 | P1 | Báo kết quả bằng tay rồi sang nhóm sau | Lưu đúng kết quả; công cụ không tự bịa link hoặc xác nhận hiển thị khi thiếu link. | Chưa chạy |

<a id="kt-15"></a>

## 15. Tạm dừng, sự cố và tiếp tục

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-15-01 | P0 | Tạm dừng khi đang thao tác một nhóm | Thao tác đang chạy có thể hoàn tất; không tự chuyển nhóm nữa. | Chưa chạy |
| KT-15-02 | P0 | Tạm dừng trong thời gian chờ giữa nhóm | Hủy lần chuyển kế tiếp; giữ tiến độ. | Chưa chạy |
| KT-15-03 | P0 | Mất mạng trước khi bấm Đăng | Dừng có lỗi; không báo đã gửi. | Chưa chạy |
| KT-15-04 | P0 | Mất mạng ngay sau khi bấm Đăng | Giữ chưa rõ nếu thiếu bằng chứng; không tự thử lại gây trùng. | Chưa chạy |
| KT-15-05 | P0 | Dừng tiến trình ứng dụng trong môi trường thử khi đang gửi | Mở lại chuyển lượt đang gửi thành chưa rõ; không tự gửi lại. | Chưa chạy |
| KT-15-06 | P1 | Bỏ qua nhóm có vấn đề sau xác nhận | Ghi bỏ qua, giữ lịch sử và xử lý tiếp theo đúng lựa chọn người dùng. | Chưa chạy |
| KT-15-07 | P1 | Thông báo lỗi và thông tin nhóm đang làm | Nêu hành động tiếp theo, đúng nhóm/số thứ tự; chi tiết kỹ thuật mở riêng. | Chưa chạy |

<a id="kt-16"></a>

## 16. Chống đăng trùng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-16-01 | P0 | Cùng bài/cùng nhóm đã có lượt | Cảnh báo trước khi tạo lượt mới. | Chưa chạy |
| KT-16-02 | P0 | Cùng nội dung/ảnh nhưng lưu dưới tên bài khác | Vẫn nhận diện trùng. | Chưa chạy |
| KT-16-03 | P0 | Cùng bytes ảnh nhưng đường dẫn ảnh nhập khác | Vẫn nhận diện trùng theo ảnh, không chỉ tên tệp. | Chưa chạy |
| KT-16-04 | P1 | Nội dung chỉ khác khoảng trắng theo quy tắc chuẩn hóa | Đối chiếu trùng nhất quán; ghi rõ trường hợp thử. | Chưa chạy |
| KT-16-05 | P0 | Có lượt đã gửi hoặc chưa rõ ở đợt khác | Kiểm tra lại trước gửi; không tự gửi chéo đợt gây lặp. | Chưa chạy |
| KT-16-06 | P0 | Bấm gửi lại chính lượt đã xử lý hoặc chưa rõ | Chặn gửi lại; yêu cầu kiểm tra hoặc tạo lượt mới có xác nhận phù hợp. | Chưa chạy |
| KT-16-07 | P1 | Đăng lại có chủ đích bằng lượt mới | Chỉ cho phép sau xác nhận trùng; không thay lịch sử lượt cũ. | Chưa chạy |
| KT-16-08 | P1 | Cùng nội dung nhưng nhóm khác hoặc nội dung/ảnh thật sự khác | Không báo trùng sai theo phạm vi đối chiếu đã công bố; ID và tên nhóm chưa được tự ánh xạ. | Chưa chạy |

<a id="kt-17"></a>

## 17. Theo dõi trạng thái và duyệt bài

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-17-01 | P0 | Bài đúng link/nội dung xuất hiện trong luồng thảo luận nhóm | Có thể ghi đã hiển thị khi đủ bằng chứng. | Chưa chạy |
| KT-17-02 | P0 | Bài nằm trong phần chờ duyệt của người đăng | Ghi chờ duyệt, không coi bản tác giả nhìn thấy là bài đã được duyệt. | Chưa chạy |
| KT-17-03 | P0 | Chỉ mở được permalink nhưng thiếu bằng chứng duyệt | Giữ chưa xác minh, không tự kết luận đã duyệt. | Chưa chạy |
| KT-17-04 | P0 | Không tìm thấy bài hoặc link lỗi | Không tự coi là bị xóa/từ chối; giữ trạng thái đã biết và ghi lần kiểm tra chưa xác minh. | Chưa chạy |
| KT-17-05 | P0 | Nhiều bài giống nhau hoặc bài cũ trùng nội dung | Không nhận nhầm; khi thiếu link cần thêm bằng chứng thời gian. | Chưa chạy |
| KT-17-06 | P0 | Nhãn bài mâu thuẫn với tab đang mở | Giữ chưa xác minh, tránh kết luận từ dữ liệu đang tải. | Chưa chạy |
| KT-17-07 | P0 | Chữ Approved/Not approved trong nội dung/bình luận | Không nhận thành bằng chứng duyệt của bài. | Chưa chạy |
| KT-17-08 | P1 | Thông báo rõ bị từ chối hoặc bị gỡ của đúng bài | Ghi trạng thái tương ứng và nguồn bằng chứng. | Chưa chạy |
| KT-17-09 | P0 | Kiểm tra trong khi Facebook có bản đang soạn | Dùng tab riêng; không sửa/gửi/xóa bản nháp. | Chưa chạy |
| KT-17-10 | P1 | Kiểm tra một/nhiều bài, dừng và gặp lỗi đăng nhập | Đúng các bài đã chọn; dừng các bài chưa đọc khi yêu cầu hoặc lỗi truy cập. | Chưa chạy |
| KT-17-11 | P1 | Bật/tắt kiểm tra định kỳ và đổi khoảng chờ | Ghi nhớ lựa chọn; chỉ chạy lúc mở ứng dụng và không đang đăng; ưu tiên bài lâu chưa kiểm tra trong giới hạn mỗi đợt. | Chưa chạy |

<a id="kt-18"></a>

## 18. Bảng kết quả, tìm kiếm và bộ lọc

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-18-01 | P1 | Bảng chính năm cột, dữ liệu rỗng và dữ liệu có nhiều dòng | Dễ đọc; trạng thái rỗng có ý nghĩa, không hiển thị dữ liệu sai. | Chưa chạy |
| KT-18-02 | P1 | Tích từng bài/chọn tất cả/bỏ chọn | Không cần Ctrl/Shift; đếm đúng số bài đã tích. | Chưa chạy |
| KT-18-03 | P0 | Refresh hoặc đổi bộ lọc sau khi tích | Giữ lựa chọn còn hiện, không thao tác nhầm bài đã bị lọc ẩn. | Chưa chạy |
| KT-18-04 | P1 | Tìm theo tên bài, nội dung, nhóm, link, ghi chú | Hiển thị đúng kết quả trong phạm vi hỗ trợ. | Chưa chạy |
| KT-18-05 | P1 | Kết hợp bài, nhóm, nhãn và trạng thái | Kết quả thỏa đồng thời các điều kiện. | Chưa chạy |
| KT-18-06 | P1 | Hôm nay, 7 ngày qua, Chờ duyệt, Cần xử lý, Tất cả | Đúng phạm vi; lọc thời gian nhanh dùng ngày gửi, không thay bằng ngày tạo. | Chưa chạy |
| KT-18-07 | P1 | Khoảng ngày có cùng hai đầu và dữ liệu ở ranh giới ngày | Bao gồm cả hai đầu, theo giờ máy; kiểm tra cả ngày tạo/gửi/kiểm tra. | Chưa chạy |
| KT-18-08 | P1 | Ngày bắt đầu lớn hơn ngày kết thúc | Có hướng dẫn, không giữ lựa chọn cũ để thao tác nhầm. | Chưa chạy |
| KT-18-09 | P1 | Bài cũ không biết ngày gửi | Để trống; không bịa ngày và không cho vào bộ lọc ngày gửi bằng ngày tạo. | Chưa chạy |
| KT-18-10 | P1 | Bấm dòng, Xem chi tiết và Sao chép link | Thông tin đầy đủ thuộc đúng dòng hiện tại, độc lập với các ô tích dùng thao tác hàng loạt. | Chưa chạy |

<a id="kt-19"></a>

## 19. Link bài và ảnh minh chứng

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-19-01 | P0 | Tự nhận diện được duy nhất link bài mới đúng nhóm | Lưu đúng permalink, không lấy link bài cũ có trước lúc gửi. | Chưa chạy |
| KT-19-02 | P1 | Không nhận diện được link tự động | Để trống/giữ kết quả gửi phù hợp, không bịa link. | Chưa chạy |
| KT-19-03 | P0 | Lưu link khác nhóm, link trang nhóm hoặc miền giả | Từ chối; không thay link đang có bằng dữ liệu sai. | Chưa chạy |
| KT-19-04 | P1 | Mở bài, lấy link đang mở và sao chép link | Đúng bài/nhóm; link được chuẩn hóa trong phạm vi hỗ trợ. | Chưa chạy |
| KT-19-05 | P0 | Chụp khi trang hiện tại khác permalink đã lưu | Chặn chụp gắn nhầm bài. | Chưa chạy |
| KT-19-06 | P1 | Chụp đúng bài sau khi người dùng kiểm tra vị trí cuộn | Lưu/mở được ảnh vùng trình duyệt đang hiển thị; không coi ảnh là bằng chứng duyệt tự động. | Chưa chạy |
| KT-19-07 | P0 | Đổi permalink sau khi đã có ảnh minh chứng | Không giữ liên kết minh chứng hoặc xác nhận cũ cho bài mới. | Chưa chạy |

<a id="kt-20"></a>

## 20. Lịch sử, thời gian và tính toàn vẹn trạng thái

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-20-01 | P0 | Một lần gửi thành công qua ứng dụng | Ghi ngày gửi khi nhận kết quả, không ghi trước khi thực sự xác nhận gửi. | Chưa chạy |
| KT-20-02 | P0 | Chỉ sửa trạng thái bằng tay hoặc kiểm tra bài cũ | Không tự bịa ngày gửi thực tế. | Chưa chạy |
| KT-20-03 | P1 | Lần đầu nhận diện đã hiển thị và các lần kiểm tra sau | Ghi mốc phát hiện đầu tiên và lần kiểm tra mới nhất đúng ý nghĩa. | Chưa chạy |
| KT-20-04 | P0 | Kiểm tra chưa xác minh sau khi từng đã hiển thị | Giữ trạng thái đã biết, tách kết quả lần kiểm tra gần nhất. | Chưa chạy |
| KT-20-05 | P1 | Thay đổi từ người dùng, trình duyệt, kiểm tra và khôi phục | Có lịch sử với thời gian, nguồn, trạng thái cũ/mới và ghi chú phù hợp. | Chưa chạy |
| KT-20-06 | P0 | Ghi trạng thái đã hiển thị kèm link, giả lập lỗi ghi DB | Không để trạng thái thành công thiếu link hoặc cập nhật dở dang. | Chưa chạy |

<a id="kt-21"></a>

## 21. Xuất Excel, sao lưu và khôi phục

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-21-01 | P1 | Xuất toàn bộ kết quả đang lọc | Đúng phạm vi, tiếng Việt, trạng thái, link và các mốc thời gian. | Chưa chạy |
| KT-21-02 | P0 | Xuất các bài đã tích | Chỉ có các bài đã tích còn trong phạm vi, không lẫn bài đang được tô dòng. | Chưa chạy |
| KT-21-03 | P1 | Xuất khi không có kết quả hoặc hủy hộp thoại | Có hướng dẫn hoặc không tạo tệp ngoài ý muốn. | Chưa chạy |
| KT-21-04 | P0 | Nội dung/ghi chú mở đầu bằng =, +, -, @ | Không trở thành công thức thực thi khi mở Excel. | Chưa chạy |
| KT-21-05 | P0 | Sao lưu có bài, nhóm, ảnh, nháp và lịch sử | DB nhất quán và đủ tệp dữ liệu cần khôi phục. | Chưa chạy |
| KT-21-06 | P0 | Kiểm tra nội dung ZIP sao lưu | Không có thư mục browser/phiên đăng nhập Facebook. | Chưa chạy |
| KT-21-07 | P0 | Khôi phục trên bản sao thư mục dữ liệu rồi mở ứng dụng | Đọc lại bài/ảnh/nháp/lịch sử; không tự đăng khi khởi động, đăng nhập lại khi cần. | Chưa chạy |
| KT-21-08 | P1 | Đích xuất/sao lưu không ghi được hoặc nằm trong thư mục dữ liệu bị cấm | Báo lỗi và giữ nguyên dữ liệu gốc. | Chưa chạy |

<a id="kt-22"></a>

## 22. Cập nhật, bảo vệ dữ liệu và quyền riêng tư

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-22-01 | P0 | Mở dữ liệu bản cũ bằng bản mới trên bản sao thử | Nâng cấu trúc đúng, không mất bài, nhóm, ảnh, lịch sử và công việc. | Chưa chạy |
| KT-22-02 | P0 | Giải nén bản mới ở thư mục khác rồi chạy | Vẫn đọc đúng dữ liệu người dùng ngoài thư mục chương trình. | Chưa chạy |
| KT-22-03 | P0 | Xóa bài/nhóm gốc khi đã có lượt đăng | Lượt cũ giữ snapshot; không đổi nhầm người nhận/nội dung. | Chưa chạy |
| KT-22-04 | P0 | Đường dẫn tệp vượt ra ngoài thư mục dữ liệu | Từ chối đường dẫn không thuộc dữ liệu ứng dụng. | Chưa chạy |
| KT-22-05 | P0 | Kiểm tra gói phát hành và dữ liệu được đưa vào repo | Không có mật khẩu, cookie, phiên Facebook hoặc DB người dùng thật. | Chưa chạy |
| KT-22-06 | P1 | Lỗi tệp dữ liệu/thiếu quyền trong môi trường thử | Có thông tin chẩn đoán; không âm thầm ghi nhận thành công hoặc xóa dữ liệu để chữa lỗi. | Chưa chạy |

<a id="kt-23"></a>

## 23. Khả dụng với người mới và hiển thị

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-23-01 | P1 | Người lần đầu đi từ đăng nhập đến một bài thử | Tự tìm được thao tác chính qua hướng dẫn; ghi lại chỗ phải nhờ hỗ trợ. | Chưa chạy |
| KT-23-02 | P1 | Cửa sổ 1280×850 và 980×680 | Nút tiếp tục/bắt đầu luôn tiếp cận được; bảng chính không buộc kéo ngang. | Chưa chạy |
| KT-23-03 | P2 | Windows phóng chữ 100%, 125%, 150% | Kiểm tra nút, hộp thoại và nội dung không bị che đến mức không thao tác được. | Chưa chạy |
| KT-23-04 | P1 | Tên bài/nhóm dài và ghi chú nhiều dòng | Có cách xem đủ nội dung, không phải đoán bài đang chọn. | Chưa chạy |
| KT-23-05 | P1 | Phân biệt kết quả bằng chữ và màu | Không phụ thuộc riêng màu sắc để hiểu trạng thái. | Chưa chạy |
| KT-23-06 | P1 | Nhấn Tab, Space, Enter và dùng chuột | Điều hướng và tích chọn phù hợp; Enter không gây gửi ngoài luồng xác nhận. | Chưa chạy |
| KT-23-07 | P1 | Thông báo cần đăng nhập, mất mạng, chưa rõ kết quả | Nêu bước tiếp theo dễ hiểu; lỗi kỹ thuật có phần chi tiết riêng. | Chưa chạy |

<a id="kt-24"></a>

## 24. Hiệu năng và chạy lâu — dành cho kỹ thuật

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-24-01 | P2 | Đo mở lần đầu và mở lại với dữ liệu thật đã ẩn danh | Ghi thời gian thực tế, xác định thao tác chậm; không treo hoặc mất dữ liệu. | Chưa chạy |
| KT-24-02 | P2 | Thử nhiều nhóm và nhiều bản ghi lịch sử trên bản sao | Tìm/lọc/cuộn còn thao tác được; đếm và chọn đúng dữ liệu. | Chưa chạy |
| KT-24-03 | P1 | Soạn bài dài, nhiều ảnh và chuyển tab liên tục | Không mất chữ, ảnh hoặc làm sai lựa chọn bài/nhóm. | Chưa chạy |
| KT-24-04 | P1 | Chạy nhiều đợt kiểm tra mô phỏng trong thời gian dài | Không tăng tab/tiến trình mãi, không gọi chồng luồng gửi và kiểm tra. | Chưa chạy |
| KT-24-05 | P1 | Lặp mở/đóng, khôi phục nháp và dừng giữa thao tác | Không lỗi đóng Qt/worker, không rò tiến trình gây khóa dữ liệu mãi. | Chưa chạy |

<a id="kt-25"></a>

## 25. Nghiệm thu công việc hằng ngày

| Mã | Ưu tiên | Đầu mục kiểm thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|---|
| KT-25-01 | P0 | Soạn bài A có nhiều ảnh, chọn một nhóm thử và đăng | Đúng bài/nhóm/ảnh; không gửi nhầm, không gửi lặp. | Chưa chạy |
| KT-25-02 | P0 | Soạn bài B khác A, đăng nhiều nhóm theo nhãn và bỏ tích một nhóm | Chỉ gửi nhóm còn tích, đúng nội dung B và thứ tự. | Chưa chạy |
| KT-25-03 | P0 | Một bài vào chờ duyệt, phần còn lại vẫn chạy | Kết quả trung thực, không yêu cầu xác nhận từng nhóm. | Chưa chạy |
| KT-25-04 | P0 | Tạm dừng đợt, đóng/mở và tiếp tục | Giữ tiến độ, không tự gửi lại các lượt đã xử lý/chưa rõ. | Chưa chạy |
| KT-25-05 | P1 | Tìm bài trong ngày, tích chọn, kiểm tra trạng thái và xuất Excel | Người dùng hoàn thành được mà không cần Ctrl/Shift hoặc hiểu lỗi kỹ thuật. | Chưa chạy |
| KT-25-06 | P0 | Đóng khi đang soạn rồi mở lại khôi phục | Đủ bản nháp, chưa tự đăng; người dùng hiểu khi nào cần bấm Lưu bài/Bắt đầu. | Chưa chạy |

## Điều kiện chốt một đợt kiểm thử

- Các ca P0 trong phạm vi phát hành đã đạt; không gộp ca bị chặn vào số ca đạt.
- Lỗi P1 ảnh hưởng luồng chính đã được xử lý hoặc nêu rõ giới hạn còn lại; P2 có ghi nhận để theo dõi.
- Chạy lại ca lỗi và phần liên quan sau khi sửa. Kiểm tra hồi quy các luồng đăng, giữ dữ liệu, chống trùng và nháp khi thay đổi liên quan.
- Phân biệt kết quả local/mô phỏng, gói Windows và Facebook thật. Chỉ mở được link hoặc bấm Đăng không đủ để chốt bài đã được duyệt.
- Bản phát hành có link ZIP, phiên bản, mã nguồn tương ứng, checksum và bằng chứng kiểm tra khởi động `.exe`.

## Mẫu ghi lỗi

| Trường | Nội dung cần điền |
|---|---|
| Mã ca / mã lỗi | Ví dụ KT-15-04 / BUG-001 |
| Phiên bản và môi trường | Bản ứng dụng, Windows, DPI, mô phỏng hay Facebook thật |
| Điều kiện ban đầu | Bài/nhóm thử, trạng thái trước thao tác; không ghi thông tin đăng nhập |
| Các bước | Các thao tác theo thứ tự để tái hiện |
| Mong đợi / thực tế | Chép mong đợi từ ca thử, mô tả thực tế quan sát |
| Bằng chứng | Ảnh, ghi chú, thời điểm và log phù hợp |
| Mức ảnh hưởng | Mất dữ liệu, gửi sai/trùng, chặn công việc hay bất tiện |
| Kiểm tra lại | Phiên bản sửa, người kiểm tra, kết quả và ngày |

## Tổng hợp sau khi chạy

| Tổng ca | Đạt | Không đạt | Bị chặn | Không áp dụng | Chưa chạy |
|---|---|---|---|---|---|
| 180 | 0 | 0 | 0 | 0 | 180 |

Ngoài phạm vi chức năng bản 0.7.0: hẹn giờ đăng khi ứng dụng đóng, ứng dụng di động, nhiều người dùng và bảo đảm vượt hạn chế/kiểm duyệt Facebook. Không ghi các mục này thành tính năng đã có.
