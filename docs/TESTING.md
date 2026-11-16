# Danh sách và kết quả kiểm thử

Ngày kiểm tra: **16/11/2026 (Asia/Saigon)**.

Kết quả: **60 passed, 0 failed, 0 skipped** trong **15.73 giây**. Kiểm tra mã `ruff check .`, định dạng `ruff format --check .` và `git diff --check` đều đạt.

Môi trường: Linux, Python 3.12.14, PySide6 6.12.0 (Qt offscreen), Playwright 1.65.2 với Chromium headless, pytest 9.2.0, openpyxl 3.1.5. Các ca giao diện dùng widget Qt thật; các ca trình duyệt chạy Chromium thật với trang HTML mô phỏng. Không đăng nhập hay đăng bài lên Facebook thật.

Mỗi **lượt đăng/task hiện tại là một bài + một nhóm**. Một bài đăng nhiều nhóm tương ứng nhiều lượt. Bản hiện tại chưa có chọn nhiều nhóm trong một lần, chạy task song song hoặc hẹn giờ tự đăng. Kết quả test không xác nhận các chức năng chưa được xây dựng này.

## Danh sách kiểm tra đã chạy

Một dòng có thể bao gồm nhiều test tham số hóa; tổng số thực tế do pytest báo là 60. “Đạt” dưới đây chỉ áp dụng cho phạm vi tự động đã nêu.

| Mã | Cần kiểm tra | Kết quả mong đợi | Kết quả | Test đối chiếu |
|---|---|---|---|---|
| A01 | Lưu nội dung tiếng Việt và định dạng | Mở lại còn nội dung, in đậm và cỡ chữ | Đạt | `test_ui.py::test_editor_groups_history_and_shutdown` |
| A02 | Tiêu đề/nội dung trống | Báo lỗi, không tạo bài không hợp lệ | Đạt | `test_storage.py::test_unique_groups_and_required_fields` |
| A03 | Thêm ảnh, xóa tệp ảnh gốc | Bản ảnh trong ứng dụng vẫn tồn tại | Đạt | `test_storage.py::test_images_are_owned_and_preserved` |
| A04 | Một bài → ba nhóm | Ba lượt riêng, trạng thái/link/ảnh không lẫn | Đạt | `test_tasks.py::test_one_post_three_groups_have_independent_status_links_and_evidence` |
| A05 | Hai bài → ba nhóm mỗi bài | Sáu lượt, đúng bài, nhóm, ảnh và hashtag | Đạt | `test_tasks.py::test_two_posts_three_groups_keep_correct_content_tags_and_images` |
| A06 | Tạo sáu lượt qua nút giao diện | Bảng hiện đủ sáu lượt và chọn đúng lượt mới | Đạt | `test_task_ui.py::test_create_six_tasks_using_ui` |
| A07 | Tạo trùng bài/nhóm, chọn Không/Có | Hủy hoặc tạo thêm đúng theo lựa chọn | Đạt | `test_task_ui.py::test_duplicate_task_requires_user_choice` |
| A08 | Tạo task với bài đang sửa chưa lưu | Yêu cầu lưu trước, không tạo task từ dữ liệu cũ | Đạt | `test_task_ui.py::test_task_creation_rejects_unsaved_selected_post` |
| A09 | Tạo task khi chưa có bài/nhóm | Báo lỗi, không tạo bản ghi dở dang | Đạt | `test_task_ui.py::test_task_creation_requires_post_and_group`, `test_tasks.py::test_missing_input_creates_no_partial_task` |
| A10 | Sửa bài hoặc nhóm sau khi tạo task | Task cũ giữ nội dung cũ; task mới lấy dữ liệu mới | Đạt | `test_tasks.py::test_editing_post_and_group_only_affects_future_tasks` |
| A11 | Xóa bài và nhóm gốc | Lịch sử và nội dung đã chốt vẫn còn | Đạt | `test_storage.py::test_snapshot_survives_changes_and_deletion` |
| A12 | Đóng/mở cơ sở dữ liệu | Cả sáu task và ghi chú vẫn nguyên vẹn | Đạt | `test_tasks.py::test_all_tasks_persist_when_database_is_reopened` |
| A13 | Chuyển task rồi lưu link/trạng thái/ghi chú | Chỉ task đang chọn thay đổi, clipboard đúng dữ liệu | Đạt | `test_task_ui.py::test_switch_tasks_routes_link_note_and_clipboard_to_correct_task` |
| A14 | Kết quả điền/lấy link trả về sau khi chọn task khác | Cập nhật task gốc, không ghi vào task vừa chọn | Đạt | `test_task_ui.py::test_delayed_browser_result_updates_origin_task_after_selection_changes` |
| A15 | Kết quả chụp ảnh về sau khi chuyển task | Ảnh chỉ gắn vào task gốc, không tự xác nhận đã đăng | Đạt | `test_task_ui.py::test_screenshot_result_updates_only_origin_task` |
| A16 | Điền lại task đang chờ duyệt | Không hạ trạng thái về đã chuẩn bị | Đạt | `test_task_ui.py::test_filling_again_does_not_downgrade_pending_task` |
| A17 | Gọi thao tác thứ hai khi trình duyệt bận; giả lập lỗi | Chặn thao tác thứ hai; sau lỗi cho phép thử lại | Đạt | `test_task_ui.py::test_busy_browser_blocks_second_task_and_buttons_reenable_after_failure` |
| A18 | Lọc khiến task được chọn bị ẩn | Không cho thao tác với task không còn hiển thị | Đạt | `test_task_ui.py::test_hidden_history_row_cannot_be_used_for_posting` |
| A19 | Link nhóm sai miền/HTTP/thông tin đăng nhập/cổng sai | Từ chối; nhóm trùng cũng bị chặn | Đạt | `test_storage.py::test_reject_invalid_group`, `test_unique_groups_and_required_fields` |
| A20 | Các dạng permalink, link bảng tin hoặc khác nhóm | Chuẩn hóa link bài hợp lệ; từ chối bảng tin/khác nhóm | Đạt | `test_storage.py::test_normalize_and_permalink`, `test_reject_non_permalink` |
| A21 | Xác nhận đã hiển thị khi chưa có link hoặc trạng thái sai | Từ chối, giữ dữ liệu hợp lệ | Đạt | `test_storage.py::test_status_requires_actual_permalink` |
| A22 | Cập nhật task bằng link sai nhóm | Không lưu một phần trạng thái/ghi chú; task khác không đổi | Đạt | `test_tasks.py::test_invalid_update_is_atomic_and_does_not_touch_other_tasks` |
| A23 | Đổi permalink sau khi lưu minh chứng | Bỏ liên kết ảnh cũ, yêu cầu xác nhận bài mới; không xóa file lịch sử | Đạt | `test_tasks.py::test_changing_post_link_invalidates_old_evidence_and_confirmation` |
| A24 | Đổi sang cách viết khác của cùng permalink | Giữ minh chứng và trạng thái của cùng bài | Đạt | `test_tasks.py::test_equivalent_permalink_keeps_existing_evidence` |
| A25 | Đổi link khi đang chọn “Đã hiển thị” | Hỏi xác nhận lại; chọn Không giữ link cũ | Đạt | `test_task_ui.py::test_new_permalink_on_published_task_requires_confirmation` |
| A26 | Link đổi trong lúc chụp màn hình | Từ chối ảnh trả về từ link cũ | Đạt | `test_task_ui.py::test_stale_screenshot_does_not_attach_to_changed_permalink` |
| A27 | Điền tiếng Việt, nhiều ảnh, hashtag | Đúng nội dung/ảnh; không bấm nút Đăng | Đạt (mô phỏng) | `test_browser.py::test_fill_unicode_multiple_images_without_submit` |
| A28 | Điền hai bài vào hai nhóm lần lượt | Mỗi nhóm nhận đúng nội dung và ảnh của bài tương ứng | Đạt (mô phỏng) | `test_browser.py::test_two_different_posts_fill_their_own_groups_sequentially` |
| A29 | Trình duyệt ở sai nhóm | Chặn trước khi sửa ô nội dung | Đạt (mô phỏng) | `test_browser.py::test_fill_rejects_wrong_group_before_modifying_composer` |
| A30 | Ô đã có nội dung, thiếu ô hoặc nhiều ô soạn | Không ghi đè/đoán ô soạn | Đạt (mô phỏng) | `test_browser.py::test_refuse_overwrite_existing_draft`, `test_refuse_ambiguous_dialogs`, `test_missing_or_ambiguous_composer_is_rejected` |
| A31 | Thiếu file ảnh, ô chỉ hỗ trợ một file | Báo lỗi trước khi thay nội dung hoặc tải một phần ảnh | Đạt (mô phỏng) | `test_browser.py::test_refuse_missing_attachment_without_changing_text`, `test_multiple_attachments_reject_single_file_input_without_modification` |
| A32 | Mở ô tải ảnh qua “Ảnh/video” hoặc “Photo/video” | Tìm đúng nút, tải ảnh đúng thứ tự, không bấm Đăng | Đạt (mô phỏng) | `test_browser.py::test_photo_button_fallback_uploads_images_in_selected_order` |
| A33 | Lấy link, chụp đúng/sai bài | Lấy link đúng nhóm; chụp đúng permalink; từ chối bảng tin/khác bài | Đạt (mô phỏng) | `test_browser.py::test_capture_refuses_other_post_and_writes_viewport`, `test_read_link_rejects_feed_or_different_group` |
| A34 | Xuất Excel nhiều task và dữ liệu giống công thức | Đủ sáu lượt, không trộn nội dung, chuỗi công thức không chạy | Đạt | `test_tasks.py::test_excel_exports_each_post_group_pair_once`, `test_storage.py::test_export_neutralizes_formula_and_keeps_unicode` |
| A35 | Sao lưu/khôi phục và bảo vệ tệp dữ liệu | Khôi phục đủ sáu lượt và ảnh; ZIP không chứa phiên Facebook; chặn đường dẫn ngoài dữ liệu | Đạt | `test_tasks.py::test_backup_restore_keeps_all_tasks_and_uploaded_images`, `test_storage.py::test_backup_consistent_and_excludes_session`, `test_images_are_owned_and_preserved` |
| A36 | Đóng giao diện khi worker đang chạy | Worker kết thúc trước khi cửa sổ bị hủy | Đạt | `test_ui.py::test_editor_groups_history_and_shutdown` và fixture `window` |

Kiểm tra bổ sung khi đóng gói: `test_packaging.py::test_packaging_smoke_exits_cleanly_with_qt_and_chromium` chạy ứng dụng trong tiến trình riêng, kiểm tra Qt mở/đóng, Chromium tải trang, tạo ảnh PNG và tiến trình thoát với mã 0. Ca này chạy từ mã Python trên Linux; kiểm tra file `.exe` thực tế trên Windows là bước riêng trong workflow **Build Windows** và kết quả nằm tại trang phát hành.

## Lỗi đã tái hiện và sửa

1. **Đổi link bài nhưng vẫn dùng ảnh/xác nhận của bài cũ.** Giờ đổi sang bài khác sẽ bỏ liên kết minh chứng cũ và đưa trạng thái đã hiển thị về đã chuẩn bị nếu chưa xác nhận lại. Đổi cách viết của cùng permalink không làm mất ảnh.
2. **Task bị ẩn do bộ lọc vẫn thao tác được.** Giờ yêu cầu chọn một dòng đang hiển thị.
3. **Ảnh chụp về muộn sau khi permalink đổi bị gắn nhầm.** Giờ đối chiếu link kết quả với link đang lưu; nếu khác sẽ báo cần chụp lại.
4. **Nút Ảnh/video không tìm được trong nhánh tải ảnh dự phòng.** Selector regex cũ không xử lý được dấu `/`. Đã thay bằng bộ chọn tên chính xác, kiểm tra cả tiếng Việt và tiếng Anh.

Ba lỗi đầu được tái hiện bằng lượt chạy 22 test mới: **19 đạt, 3 lỗi** trước khi sửa. Lỗi thứ tư được tái hiện sau đó trong test trình duyệt của nhánh mở nút tải ảnh. Các ca tương ứng đều đạt trong lượt chạy cuối.

## Kết quả gói Windows v0.1.0

Workflow [Build Windows #43845312660](https://github.com/Trung27012003/facebook-helper/actions/runs/43845312660) đã thành công trên `windows-latest` ở mã nguồn `45040167b42eef414ed87227cc791e754b2f7287`.

File `.exe` đã qua kiểm tra tự động: `ok=true`, `qt_started=true`, `tabs=4`, `worker_stopped=true`; Chromium đóng kèm phiên bản `159.0.8154.6` mở được trang thử và tạo PNG. Kiểm tra dùng Qt offscreen trên runner Windows; chưa thay thế thử nghiệm tương tác trên máy cá nhân hoặc đăng bài Facebook thật.

[Tải ZIP Windows 64-bit](https://github.com/Trung27012003/facebook-helper/releases/download/v0.1.0/FacebookHelper-Windows-x64.zip), dung lượng **445.825.127 byte** (khoảng 425 MiB). SHA256: `78c1c6d17b2be97bbc3767d0ec54d661369673d318f79f61a622be54ec95376b`.

## Danh sách cần kiểm tra trên Facebook thật / Windows

**Chưa hoàn tất kiểm tra tương tác thực tế** vì phiên này không có tài khoản Facebook đã đăng nhập và nhóm dùng thử. Gói `.exe` và Chromium đã qua kiểm tra khởi động trên runner Windows như ghi ở trên; các ca dưới đây cần thao tác thực tế bổ sung.

Chuẩn bị: một máy Windows, tài khoản của người kiểm thử, hai nhóm được phép thử đăng (một nhóm duyệt trực tiếp, một nhóm chờ duyệt), hai bài thử khác nhau với hai ảnh mỗi bài. Chỉ đăng sau khi người kiểm thử xác nhận trong Facebook.

| Mã | Thao tác cần thử | Tiêu chí đạt | Trạng thái |
|---|---|---|---|
| M01 | Cài mới bằng README; chạy `start.bat`; mở lại | Qt mở được, Chromium khởi động, dữ liệu còn sau khi mở lại | Chưa test Windows |
| M02 | Tạo bản `.exe` bằng workflow và chạy trên máy không cài Python | Không thiếu Qt/Chromium; mở được giao diện và trình duyệt | Đã qua khởi động tự động trên runner Windows; chưa test trên máy cá nhân không cài Python |
| M03 | Đăng nhập, đóng/mở lại ứng dụng, rồi đăng xuất | Phiên được giữ trong hồ sơ riêng; đăng xuất có hiệu lực | Chưa test Facebook thật |
| M04 | Bài A → hai nhóm, từng nhóm một | Nội dung, xuống dòng, ảnh và thứ tự đúng; task/link/ảnh minh chứng độc lập | Chưa test Facebook thật |
| M05 | Bài A → nhóm 1; bài B → nhóm 2 | Không lẫn chữ, ảnh và hashtag giữa hai bài | Chưa test Facebook thật |
| M06 | Thử nhóm chờ duyệt rồi duyệt bài | Không báo đã hiển thị khi mới gửi; sau duyệt lấy được permalink đúng | Chưa test Facebook thật |
| M07 | Lấy link từ bài đang mở; mở lại; chụp và xem minh chứng | Link dẫn đúng bài; ảnh nhìn thấy đúng bài, không phải màn hình đăng nhập/lỗi | Chưa test Facebook thật |
| M08 | Đổi giao diện Facebook sang Anh/Việt, mở mục Ảnh/video | Điền và đính kèm được hoặc có thông báo để dùng cách thủ công | Chưa test Facebook thật |
| M09 | Mất mạng, đóng tab hoặc đóng trình duyệt giữa thao tác | Ứng dụng không treo; báo lỗi; có thể mở lại và thử tiếp | Chưa test Facebook thật |
| M10 | Sao chép bài, mở thư mục ảnh và đăng thủ công | Nội dung đúng, thư mục chỉ chứa ảnh đúng task, tên có thứ tự | Chưa test tương tác desktop thật |
| M11 | Chọn/đổi font, màu, cỡ chữ; xem ảnh và xuất báo cáo trên Windows | Bản nháp hiển thị đúng; ảnh mở được; Excel mở được | Chưa test Windows |

Nếu gặp lỗi, ghi rõ mã ca, phiên bản Windows, ngôn ngữ Facebook, thao tác, kết quả mong đợi/thực tế và ảnh lỗi. Không gửi cookie, mật khẩu hoặc thư mục `browser/`.

## Chạy lại

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
ruff check .
ruff format --check .
QT_QPA_PLATFORM=offscreen pytest -q --junitxml=work/test-results.xml
```

PowerShell: đặt `$env:QT_QPA_PLATFORM = 'offscreen'`, tạo thư mục `work` nếu chưa có, rồi chạy `python -m pytest -q --junitxml=work/test-results.xml`.

Các test dùng thư mục tạm và dữ liệu mô phỏng, không dùng cơ sở dữ liệu HR cá nhân. Log tóm tắt của lượt chạy này nằm ở [test-output.txt](test-output.txt).
