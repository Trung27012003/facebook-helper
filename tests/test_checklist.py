"""Additional acceptance checks selected from docs/TEST-CHECKLIST.md."""

import pytest
from PySide6.QtCore import Qt


def test_deleted_original_draft_cannot_overwrite_reused_post_id(window, store):
    original = store.save_post(None, "Bài A", "<p>Nội dung A</p>", "Nội dung A", "", [])
    window.refresh_posts()
    item = next(
        window.post_list.item(i)
        for i in range(window.post_list.count())
        if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == original
    )
    window.load_post(item)
    window.title.setText("Nháp của A")
    window.content.setHtml("<p>Nội dung A chưa xong</p>")
    assert window.autosave_draft()
    # A prior-session draft is left unrecovered, then the original is deleted.
    window.active_draft_id = None
    window.dirty = False
    store.delete_post(original)
    replacement = store.save_post(None, "Bài B cần giữ", "<p>Nội dung B</p>", "Nội dung B", "", [])
    assert replacement == original, "SQLite reuses the largest deleted INTEGER PRIMARY KEY"
    before = store.post(replacement)
    window.recover_draft()
    assert window.post_id is None, (
        "A deleted original must recover as a new post even if its numeric ID is reused"
    )
    window.save_post()
    assert store.post(replacement) == before


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "  =", "\t+", "\n@"])
def test_excel_user_text_is_not_executable_formula(store, job, tmp_path, prefix):
    from openpyxl import load_workbook

    store.update_job(job, note=prefix + 'HYPERLINK("https://example.com")')
    path = tmp_path / "formula.xlsx"
    store.export_excel(path)
    book = load_workbook(path)
    try:
        assert book.active["H2"].data_type == "s"
        assert book.active["H2"].value.startswith("'")
    finally:
        book.close()


def test_backup_restores_unsaved_draft_images_and_status_history(window, store, task_data, tmp_path):
    import json
    import zipfile

    from facebook_helper.storage import Store

    window.title.setText("Nháp trong bản sao lưu")
    window.content.setHtml("<p><b>Chưa bấm Lưu bài</b></p>")
    post = store.post(task_data[0][0])
    window.add_image_item(post["images"][0])
    window.autosave_draft()
    job_id = store.create_job(post["id"], task_data[1][0])
    store.update_job(job_id, source="browser", status="submitted")
    archive_path = tmp_path / "backup.zip"
    store.backup(archive_path)
    restored_root = tmp_path / "restored"
    with zipfile.ZipFile(archive_path) as archive:
        assert not any(name.startswith("browser/") for name in archive.namelist())
        archive.extractall(restored_root)
    restored = Store(restored_root)
    try:
        drafts = json.loads(restored.preference("editor_drafts"))
        assert drafts == window.stored_drafts()
        draft = next(iter(drafts.values()))
        assert "<b>" in draft["html"]
        assert restored.asset(draft["images"][0]).read_bytes() == store.asset(post["images"][0]).read_bytes()
        assert restored.events(job_id) == store.events(job_id)
    finally:
        restored.close()


def test_existing_original_is_updated_only_when_draft_identity_matches(window, store):
    original = store.save_post(None, "Gốc", "<p>Gốc</p>", "Gốc", "", [])
    window.refresh_posts()
    window.load_post(window.post_list.item(0))
    window.title.setText("Nháp của đúng bài")
    window.autosave_draft()
    assert next(iter(window.stored_drafts().values()))["post_uid"] == store.post(original)["uid"]
    window.active_draft_id = None
    window.dirty = False
    window.recover_draft()
    assert window.post_id == original
    window.save_post()
    assert store.post(original)["title"] == "Nháp của đúng bài" and len(store.posts()) == 1


def test_legacy_draft_without_identity_recovers_as_copy(window, store):
    import json

    original = store.save_post(None, "Bài cần giữ", "<p>Hiện tại</p>", "Hiện tại", "", [])
    before = store.post(original)
    store.set_preference(
        "editor_drafts",
        json.dumps(
            {
                "old": {
                    "post_id": original,
                    "title": "Nháp cũ",
                    "html": "<p>Nháp cũ</p>",
                    "plain": "Nháp cũ",
                    "tags": "",
                    "images": [],
                    "saved_at": "2026-11-16T00:00:00+00:00",
                }
            }
        ),
    )
    window.recover_draft()
    assert window.post_id is None
    window.save_post()
    assert store.post(original) == before and len(store.posts()) == 2


def test_post_identity_survives_reopen_and_is_not_reused(store):
    from facebook_helper.storage import Store

    original = store.save_post(None, "A", "<p>A</p>", "A", "", [])
    uid = store.post(original)["uid"]
    reopened = Store(store.root)
    try:
        assert reopened.post(original)["uid"] == uid
        reopened.delete_post(original)
        other = reopened.save_post(None, "B", "<p>B</p>", "B", "", [])
        assert other == original and reopened.post(other)["uid"] != uid
    finally:
        reopened.close()


def test_library_duplicate_delete_and_switch_preserve_correct_saved_posts(window, store, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window.title.setText("Bản gốc")
    window.content.setHtml("<p><b>Nội dung gốc</b></p>")
    original = window.save_post()
    before = store.post(original)
    window.duplicate_post()
    window.content.setHtml("<p>Nội dung riêng của bản sao</p>")
    clone = window.save_post()
    assert clone != original and store.post(original) == before
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.delete_post()
    assert store.post(clone)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.delete_post()
    with pytest.raises(ValueError):
        store.post(clone)
    assert store.post(original) == before


def test_group_edit_and_delete_confirmation_preserve_job_snapshot(window, store, job, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    before = store.job(job)
    window.refresh_groups()
    window.load_group(window.group_list.item(0))
    group_id = window.group_id
    window.group_name.setText("Tên nhóm đã sửa")
    window.group_notes.setPlainText("Quy định thử")
    window.save_group()
    assert next(g for g in store.groups() if g["id"] == group_id)["notes"] == "Quy định thử"
    assert store.job(job) == before
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.delete_group()
    assert any(g["id"] == group_id for g in store.groups())
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.delete_group()
    assert not any(g["id"] == group_id for g in store.groups())
    assert store.job(job)["group_url"] == before["group_url"]


def test_image_order_and_hashtags_survive_draft_restore(window, store, task_data):
    images = [store.post(p)["images"][0] for p in task_data[0]]
    window.title.setText("Nháp nhiều ảnh")
    window.content.setHtml("<p><b>Tuyển người 🚀</b></p>")
    window.tags.setText("#KỹThuật #PLC")
    for image in images:
        window.add_image_item(image)
    window.images.setCurrentRow(0)
    window.move_image(1)
    expected = list(reversed(images))
    window.autosave_draft()
    draft = next(iter(window.stored_drafts().values()))
    assert draft["images"] == expected and draft["tags"] == "#KỹThuật #PLC"
    window.active_draft_id = None
    window.dirty = False
    window.recover_draft()
    assert [window.images.item(i).data(Qt.ItemDataRole.UserRole) for i in range(2)] == expected
    assert [window.images.item(i).text() for i in range(2)] == ["Ảnh 1", "Ảnh 2"]
    assert "🚀" in window.content.toPlainText()
    assert window.tags.text() == "#KỹThuật #PLC"


def test_reject_nonimage_and_oversized_valid_image(store, tmp_path, app):
    from PySide6.QtGui import QImage

    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Không đọc được"):
        store.import_image(bad)
    large = tmp_path / "large.png"
    image = QImage(2, 2, QImage.Format.Format_RGB32)
    assert image.save(str(large))
    with large.open("ab") as f:
        f.write(b"\x00" * (30 * 1024 * 1024))
    with pytest.raises(ValueError, match="30 MB"):
        store.import_image(large)
    assert list((store.root / "images").iterdir()) == []


def test_second_instance_is_blocked_without_changing_active_sending_job(store, job):
    import os
    import subprocess
    import sys

    from PySide6.QtCore import QLockFile

    lock = QLockFile(str(store.root / "app.lock"))
    assert lock.tryLock(100)
    store.update_job(job, status="sending")
    before = store.job(job)
    code = """
import sys
from PySide6.QtWidgets import QMessageBox
QMessageBox.warning=lambda *args: print("SECOND_INSTANCE_BLOCKED")
from facebook_helper.__main__ import main
sys.argv=["facebook-helper","--data-dir",sys.argv[1]]
sys.exit(main())
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, str(store.root)],
            capture_output=True,
            text=True,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            timeout=30,
        )
        assert result.returncode == 1 and "SECOND_INSTANCE_BLOCKED" in result.stdout
        assert store.job(job) == before
    finally:
        lock.unlock()


@pytest.mark.parametrize("host", ["facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"])
def test_supported_group_hosts_and_share_query_normalize(host):
    from facebook_helper.domain import normalize_group

    assert (
        normalize_group(f"https://{host}/groups/nhom-thu/?ref=share")
        == "https://www.facebook.com/groups/nhom-thu/"
    )


def test_summernote_undo_redo_restores_unicode_content(window):
    window.content.setPlainText("Nội dung ban đầu")
    before = window.content.toPlainText()
    window.content.evaluate("editorApi.command('insertText',' Thêm chữ Việt 🚀')")
    after = window.content.toPlainText()
    assert after != before and "Thêm chữ Việt" in after
    window.content.evaluate("editorApi.command('undo')")
    assert window.content.toPlainText() == before
    window.content.evaluate("editorApi.command('redo')")
    assert window.content.toPlainText() == after


@pytest.mark.parametrize("field", ["created_at", "sent_at", "checked_at"])
def test_date_filters_include_both_boundaries_and_exclude_adjacent_days(window, store, task_data, field):
    from datetime import datetime

    from PySide6.QtCore import QDate

    tz = datetime.now().astimezone().tzinfo
    values = [
        datetime(2026, 11, 16, 23, 59, tzinfo=tz),
        datetime(2026, 11, 17, 0, 0, tzinfo=tz),
        datetime(2026, 11, 17, 23, 59, tzinfo=tz),
        datetime(2026, 11, 18, 0, 0, tzinfo=tz),
    ]
    ids = [store.create_job(p, g) for p in task_data[0] for g in task_data[1][:2]]
    with store.db:
        for job_id, value in zip(ids, values):
            store.db.execute(f"UPDATE jobs SET {field}=? WHERE id=?", (value.isoformat(), job_id))
    view = window.post_manager
    view.date_field.setCurrentIndex(view.date_field.findData(field))
    view.start.setDate(QDate(2026, 11, 17))
    view.end.setDate(QDate(2026, 11, 17))
    view.use_dates.setChecked(True)
    assert {j["id"] for j in view.filtered_jobs} == {ids[1], ids[2]}


def test_seven_day_filter_includes_today_minus_six_not_minus_seven(window, store, task_data):
    from datetime import datetime, timedelta

    now = datetime.now().astimezone()
    ids = [store.create_job(task_data[0][0], g) for g in task_data[1]]
    with store.db:
        for job_id, days in zip(ids, [0, 6, 7]):
            store.db.execute(
                "UPDATE jobs SET sent_at=? WHERE id=?", ((now - timedelta(days=days)).isoformat(), job_id)
            )
    view = window.post_manager
    view.quick_filter("week")
    assert {j["id"] for j in view.filtered_jobs} == set(ids[:2])


def test_library_search_reads_full_body_not_only_tooltip(window, store):
    text = "Mở đầu " * 70 + "TừKhóaNằmCuốiBài"
    post = store.save_post(None, "Tên ngắn", "<p>" + text + "</p>", text, "", [])
    window.refresh_posts()
    window.search.setText("từkhóanằmcuốibài")
    item = next(
        window.post_list.item(i)
        for i in range(window.post_list.count())
        if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == post
    )
    assert not item.isHidden(), "Search must match the body after its 250-character tooltip preview"


def test_undo_after_switching_saved_posts_cannot_restore_previous_post(window, store, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    first = store.save_post(None, "A", "<p>Nội dung A</p>", "Nội dung A", "", [])
    second = store.save_post(None, "B", "<p>Nội dung B</p>", "Nội dung B", "", [])
    window.refresh_posts()

    def item(post_id):
        return next(
            window.post_list.item(i)
            for i in range(window.post_list.count())
            if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == post_id
        )

    window.load_post(item(first))
    window.content.evaluate("editorApi.command('insertText',' Sửa A')")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.load_post(item(second))
    before = window.content.toHtml()
    window.content.evaluate("editorApi.command('undo')")
    assert window.content.toHtml() == before and "Nội dung A" not in window.content.toPlainText()
    window.content.evaluate("editorApi.command('redo')")
    assert window.content.toHtml() == before


def test_library_italic_underline_and_link_survive_save_reload(window, store):
    window.title.setText("Bài có liên kết")
    window.content.setPlainText("Ứng tuyển")
    window.content.selectAll()
    window.content.evaluate("editorApi.command('italic')")
    window.content.evaluate("editorApi.command('underline')")
    window.content.evaluate(
        "editorApi.command('createLink',{text:'Ứng tuyển',url:'https://example.com/jobs',isNewWindow:true})"
    )
    post_id = window.save_post()
    html = store.post(post_id)["html"]
    assert "https://example.com/jobs" in html
    window.load_post(window.post_list.item(0))
    assert "Ứng tuyển" in window.content.toPlainText()
    assert "https://example.com/jobs" in window.content.toHtml()


def test_switching_all_tabs_keeps_unsaved_editor_content(window):
    window.title.setText("Nháp đang soạn")
    window.content.setHtml("<p><b>Không mất khi chuyển tab</b></p>")
    before = window.content.toHtml()
    for index in [1, 2, 3, 4, 0]:
        window.tabs.setCurrentIndex(index)
        assert window.content.toHtml() == before and window.dirty
        assert not window.queue_active


def test_quick_start_button_reopens_guide_without_losing_editor(window):
    from PySide6.QtWidgets import QPushButton

    window.title.setText("Đang soạn")
    window.content.setHtml("<p><b>Giữ nội dung</b></p>")
    before = window.content.toHtml()
    window.hide_quick_start()
    next(b for b in window.findChildren(QPushButton) if b.text() == "Hướng dẫn nhanh").click()
    assert not window.quick_start.isHidden() and window.content.toHtml() == before


def test_image_unicode_path_and_remove_readd_keep_owned_copy(window, store, tmp_path):
    from PySide6.QtGui import QImage

    path = tmp_path / "Ảnh tuyển dụng có dấu.png"
    image = QImage(3, 3, QImage.Format.Format_RGB32)
    assert image.save(str(path))
    relative = store.import_image(path)
    window.add_image_item(relative)
    window.images.setCurrentRow(0)
    window.remove_image()
    assert window.images.count() == 0 and store.asset(relative).is_file()
    window.add_image_item(relative)
    assert window.images.item(0).text() == "Ảnh 1"


def test_draft_timer_saves_without_manual_save(window, store):
    from PySide6.QtTest import QTest

    window.title.setText("Tự lưu theo thời gian")
    window.content.setHtml("<p>Chưa bấm nút Lưu</p>")
    QTest.qWait(1800)
    assert window.stored_drafts() and not store.posts()
    draft = next(iter(window.stored_drafts().values()))
    assert draft["title"] == "Tự lưu theo thời gian"


@pytest.mark.parametrize("accept", [False, True])
def test_discard_archived_drafts_requires_confirmation_and_keeps_current(window, store, monkeypatch, accept):
    import json

    from PySide6.QtWidgets import QMessageBox

    post = store.save_post(None, "Bài đã lưu", "<p>Giữ</p>", "Giữ", "", [])
    window.title.setText("Nháp hiện tại")
    window.content.setPlainText("Hiện tại")
    window.autosave_draft()
    active = window.active_draft_id
    drafts = window.stored_drafts()
    drafts["old"] = {
        "post_id": None,
        "title": "Cũ",
        "html": "<p>Cũ</p>",
        "plain": "Cũ",
        "tags": "",
        "images": [],
        "saved_at": "2026-11-16T00:00:00+00:00",
    }
    store.set_preference("editor_drafts", json.dumps(drafts))
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args: QMessageBox.StandardButton.Yes if accept else QMessageBox.StandardButton.No,
    )
    window.discard_recovery_drafts()
    assert active in window.stored_drafts() and bool("old" in window.stored_drafts()) != accept
    assert store.post(post)["title"] == "Bài đã lưu"


def test_recover_one_of_multiple_drafts_uses_chosen_title_and_timestamp(window, store, monkeypatch):
    import json

    from PySide6.QtWidgets import QInputDialog

    drafts = {
        key: {
            "post_id": None,
            "title": title,
            "html": f"<p>{title}</p>",
            "plain": title,
            "tags": "",
            "images": [],
            "saved_at": date,
        }
        for key, title, date in [
            ("old", "Bản cũ", "2026-11-16T00:00:00+00:00"),
            ("new", "Bản mới", "2026-11-17T00:00:00+00:00"),
        ]
    }
    store.set_preference("editor_drafts", json.dumps(drafts))
    monkeypatch.setattr(QInputDialog, "getItem", lambda parent, title, label, items, *args: (items[1], True))
    window.recover_draft()
    assert window.title.text() == "Bản cũ" and window.active_draft_id == "old"


def test_group_switch_respects_unsaved_changes(window, store, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    store.save_group(None, "Nhóm thử", "https://facebook.com/groups/thu/", "HR", "")
    window.refresh_groups()
    window.load_group(window.group_list.item(0))
    window.group_name.setText("Chưa lưu")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.new_group()
    assert window.group_name.text() == "Chưa lưu" and window.group_id is not None
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.new_group()
    assert window.group_name.text() == "" and window.group_id is None
    assert store.groups()[0]["name"] == "Nhóm thử"


@pytest.mark.parametrize("field", ["images", "group"])
def test_review_is_invalidated_by_changed_image_or_group(window, store, task_data, field):
    window.refresh_posts()
    window.refresh_groups()
    window.job_posts.setCurrentIndex(window.job_posts.findData(task_data[0][0]))
    window.set_posting_step(0)
    window.posting_next_step()
    window.posting_next_step()
    if field == "images":
        post = store.post(task_data[0][0])
        store.save_post(
            post["id"],
            post["title"],
            post["html"],
            post["plain"],
            post["tags"],
            store.post(task_data[0][1])["images"],
        )
    else:
        group = next(g for g in store.groups() if g["id"] == window.selected_group_ids()[0])
        store.save_group(
            group["id"],
            group["name"],
            "https://facebook.com/groups/changed/",
            group["category"],
            group["notes"],
        )
    with pytest.raises(ValueError, match="đã thay đổi"):
        window.posting_next_step()
    assert not store.batches()


def test_duplicate_whitespace_normalization_is_independent_of_title(store):
    group = store.save_group(None, "Nhóm", "https://facebook.com/groups/ws/", "", "")
    first = store.save_post(None, "A", "<p>Nội dung A</p>", "Nội dung A", "", [])
    store.create_job(first, group)
    second = store.save_post(None, "B", "<p>Nội dung A</p>", "Nội \n dung\tA", "", [])
    assert len(store.post_duplicates(second, [group])) == 1


def test_distinct_image_bytes_or_group_do_not_false_match(store, task_data):
    post = store.post(task_data[0][0])
    first_group, other_group = task_data[1][:2]
    store.create_job(post["id"], first_group)
    clone = store.save_post(
        None,
        "Cùng chữ, ảnh khác",
        post["html"],
        post["plain"],
        post["tags"],
        store.post(task_data[0][1])["images"],
    )
    assert not store.post_duplicates(clone, [first_group])
    assert not store.post_duplicates(post["id"], [other_group])


def test_export_checked_rows_not_current_highlighted_row(window, store, task_data, tmp_path, monkeypatch):
    from openpyxl import load_workbook
    from PySide6.QtWidgets import QFileDialog

    ids = [store.create_job(task_data[0][0], g) for g in task_data[1]]
    view = window.post_manager
    view.refresh()
    checked_id = view.table.item(0, 0).data(Qt.ItemDataRole.UserRole)
    view.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    view.table.setCurrentCell(1, 1)
    path = tmp_path / "selected.xlsx"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(path), ""))
    view.export_filtered(selected_only=True)
    book = load_workbook(path)
    try:
        rows = list(book.active.iter_rows(min_row=2, values_only=True))
        assert len(rows) == 1 and rows[0][0] == checked_id and rows[0][0] in ids
    finally:
        book.close()


def test_empty_and_cancelled_exports_create_no_file(window, store, job, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    view = window.post_manager
    view.refresh()
    view.keyword.setText("không khớp")
    notes = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: notes.append(args[2]))
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args: pytest.fail("Empty results must not open a save dialog")
    )
    view.export_filtered()
    assert notes
    view.quick_filter("all")
    before = store.jobs()
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    view.export_filtered()
    assert store.jobs() == before and not list(tmp_path.glob("*.xlsx"))


@pytest.mark.parametrize("action", ["export", "backup"])
def test_unwritable_export_or_backup_destination_keeps_data(
    window, store, job, tmp_path, monkeypatch, action
):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    target = tmp_path / "destination-is-directory"
    target.mkdir()
    before = store.jobs()
    warnings = []
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    if action == "export":
        window.export_excel()
    else:
        window.backup()
    assert warnings and store.jobs() == before


def test_long_names_multiline_notes_and_status_are_available_in_details(window, store):
    title = "Tên bài dài " * 30
    group_name = "Tên nhóm dài " * 30
    note = "Ghi chú nhiều dòng\n" * 30
    post = store.save_post(None, title, "<p>Nội dung</p>", "Nội dung", "", [])
    group = store.save_group(None, group_name, "https://facebook.com/groups/long/", "", "")
    job_id = store.create_job(post, group)
    store.update_job(job_id, status="pending", note=note)
    view = window.post_manager
    view.refresh()
    view.table.setCurrentCell(0, 1)
    view.update_details()
    assert (
        title.strip() in view.detail_text.toPlainText()
        and group_name.strip() in view.detail_text.toPlainText()
    )
    assert note.rstrip() in view.detail_text.toPlainText() and "Chờ duyệt" in view.table.item(0, 3).text()
    assert view.table.item(0, 3).foreground().color().isValid()
    store.update_job(job_id, status="published", url="https://facebook.com/groups/long/posts/123/")
    store.record_check(job_id, "unknown", "Không xác minh được lần này")
    view.refresh()
    assert (
        "Đã hiển thị" in view.table.item(0, 3).text() and "Chưa xác minh lại" in view.table.item(0, 3).text()
    )


def test_long_editor_with_ten_images_survives_repeated_tab_changes(window, store, tmp_path):
    from PySide6.QtGui import QImage

    window.title.setText("Bài dài nhiều ảnh")
    body = "Đây là nội dung tiếng Việt. " * 1000
    window.content.setPlainText(body)
    for i in range(10):
        image = QImage(4, 4, QImage.Format.Format_RGB32)
        path = tmp_path / f"img-{i}.png"
        assert image.save(str(path))
        window.add_image_item(store.import_image(path))
    for tab in [1, 2, 3, 4, 0, 3, 0]:
        window.tabs.setCurrentIndex(tab)
    assert len(window.content.toPlainText()) > 15000 and window.images.count() == 10
    assert window.autosave_draft()
    assert len(next(iter(window.stored_drafts().values()))["images"]) == 10


def test_repeated_application_start_shutdown_releases_worker_and_data_lock(tmp_path):
    import json
    import os
    import subprocess
    import sys

    root = tmp_path / "Dữ liệu kiểm thử"
    for _ in range(3):
        result = subprocess.run(
            [sys.executable, "-m", "facebook_helper", "--smoke-test", "--data-dir", str(root)],
            capture_output=True,
            text=True,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads((root / "smoke-result.json").read_text())
        assert data["worker_stopped"] and data["draft_saved"] and data["ok"]


def test_detail_and_copy_actions_use_current_row_independent_of_checkboxes(window, store, task_data, app):
    from PySide6.QtWidgets import QPushButton

    for i, group in enumerate(task_data[1][:2]):
        job_id = store.create_job(task_data[0][0], group)
        record = store.job(job_id)
        store.update_job(job_id, url=record["group_url"] + f"posts/{i + 1}/", note=f"Ghi chú {i}")
    view = window.post_manager
    view.refresh()
    window.tabs.setCurrentIndex(3)
    view.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    view.table.setCurrentCell(1, 1)
    current = view.current_job_record()
    next(b for b in view.findChildren(QPushButton) if b.text() == "Xem chi tiết").click()
    assert not view.details_panel.isHidden() and current["note"] in view.detail_text.toPlainText()
    next(b for b in view.findChildren(QPushButton) if b.text() == "Sao chép link").click()
    assert app.clipboard().text() == current["url"]


@pytest.mark.parametrize(
    "keyword",
    [
        "Vị trí đặc biệt",
        "Nội dung ở cuối",
        "Nhóm riêng biệt",
        "Ghi chú riêng",
        "/posts/123/",
        "Kết quả kiểm tra riêng",
    ],
)
def test_manager_keyword_search_covers_title_body_group_note_link_and_check_note(window, store, keyword):
    post = store.save_post(None, "Vị trí đặc biệt", "<p>Nội dung ở cuối</p>", "Nội dung ở cuối", "", [])
    group = store.save_group(None, "Nhóm riêng biệt", "https://facebook.com/groups/keyword/", "", "")
    target = store.create_job(post, group)
    store.update_job(target, note="Ghi chú riêng", url="https://facebook.com/groups/keyword/posts/123/")
    store.record_check(target, "unknown", "Kết quả kiểm tra riêng")
    other = store.save_post(None, "Khác", "<p>Không liên quan</p>", "Không liên quan", "", [])
    store.create_job(other, store.save_group(None, "Nhóm khác", "https://facebook.com/groups/other/", "", ""))
    view = window.post_manager
    view.keyword.setText(keyword.swapcase())
    assert [j["id"] for j in view.filtered_jobs] == [target]
