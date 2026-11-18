import json

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QMessageBox

from facebook_helper.ui import MainWindow


def prepare_flow(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    window.job_posts.setCurrentIndex(window.job_posts.findData(task_data[0][0]))
    window.audience_mode.setCurrentIndex(1)
    window.audience_list.item(0).setCheckState(Qt.CheckState.Checked)
    window.audience_list.item(2).setCheckState(Qt.CheckState.Checked)
    window.set_posting_step(0)


def test_four_steps_show_review_before_creating_or_sending(window, store, task_data, monkeypatch):
    prepare_flow(window, store, task_data)
    assert not store.batches()
    window.posting_next_step()
    assert window.posting_steps.currentIndex() == 1
    window.posting_next_step()
    assert window.posting_steps.currentIndex() == 2
    assert window.review_groups.count() == 2 and window.review_images.count() == 1
    assert "Lương 15 triệu" in window.review_preview.toPlainText()
    assert not store.batches()
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, data: commands.append((action, data)))
        patch.setattr(
            QMessageBox,
            "question",
            lambda *args: pytest.fail("Final review already authorizes this new batch"),
        )
        window.posting_next_step()
        assert len(store.batches()) == 1
        assert window.posting_steps.currentIndex() == 3
        assert len(commands) == 1 and commands[0][0] == "publish"
        assert commands[0][1]["group_id"] == task_data[1][0]
        window.browser_progress("Đang tải ảnh")
        assert "Nhóm 1/2" in window.current_action.text() and "Đang tải ảnh" in window.current_action.text()
        with pytest.raises(ValueError, match="Tạm dừng"):
            window.set_posting_step(0)
        window.finish_browser()
        window.pause_posting_queue()


def test_review_invalidated_when_saved_post_changes(window, store, task_data):
    prepare_flow(window, store, task_data)
    window.posting_next_step()
    window.posting_next_step()
    post = store.post(task_data[0][0])
    store.save_post(
        post["id"], post["title"], "<p>Thay đổi mức lương</p>", "Mức lương mới", "", post["images"]
    )
    with pytest.raises(ValueError, match="đã thay đổi"):
        window.posting_next_step()
    assert not store.batches() and not window.queue_active


def test_review_cancel_duplicate_does_not_start_queue(window, store, task_data, monkeypatch):
    prepare_flow(window, store, task_data)
    store.create_job(task_data[0][0], task_data[1][0])
    window.posting_next_step()
    window.posting_next_step()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.posting_next_step()
    assert not store.batches() and not window.queue_active
    assert window.posting_steps.currentIndex() == 2


def test_missing_post_or_groups_has_actionable_message(window, store, task_data):
    with pytest.raises(ValueError, match="Lưu bài"):
        window.posting_next_step()
    prepare_flow(window, store, task_data)
    window.check_audience(False)
    window.posting_next_step()
    with pytest.raises(ValueError, match="ít nhất một nhóm"):
        window.posting_next_step()


def test_post_this_article_saves_and_opens_guided_flow(window, store):
    window.title.setText("Bài mới")
    window.content.setHtml("<p><b>Tuyển kế toán</b></p>")
    window.post_this_article()
    assert store.post(window.post_id)["plain"] == "Tuyển kế toán"
    assert window.tabs.currentIndex() == 3 and window.posting_steps.currentIndex() == 1
    assert window.job_posts.currentData() == window.post_id


def test_autosave_preserves_rich_content_and_images_without_updating_saved_post(window, store, task_data):
    window.refresh_posts()
    item = next(
        window.post_list.item(i)
        for i in range(window.post_list.count())
        if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == task_data[0][0]
    )
    window.load_post(item)
    old = store.post(window.post_id)
    window.content.setHtml("<p><b>Đang chỉnh sửa lương 30 triệu</b></p>")
    window.title.setText("Bản đang sửa")
    assert window.autosave_draft()
    draft = next(iter(window.stored_drafts().values()))
    assert "30 triệu" in draft["plain"] and "<b>" in draft["html"]
    assert draft["images"] == old["images"]
    assert store.post(window.post_id) == old
    window.save_post()
    assert not window.stored_drafts() and not window.dirty
    assert "30 triệu" in store.post(window.post_id)["plain"]


def test_restart_offers_draft_recovery_without_sending_or_saving_post(window, store, app):
    window.title.setText("Nháp cần khôi phục")
    window.content.setHtml("<p><b>Tiếng Việt có định dạng</b></p>")
    assert window.autosave_draft()
    other = MainWindow(store, background=False)
    other.show()
    app.processEvents()
    try:
        assert not other.draft_recovery.isHidden()
        assert not other.dirty and other.post_id is None
        assert store.posts() == [] and store.jobs() == []
        other.recover_draft()
        assert other.title.text() == "Nháp cần khôi phục"
        assert "<b>" in other.content.toHtml()
        assert other.dirty and other.tabs.currentIndex() == 0
        assert not other.queue_active and not other.busy
    finally:
        other.dirty = False
        other.browser.submit("stop")
        assert other.browser.wait(10000)
        other.close()
        other.content.release()
        other.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_autosave_survives_close_without_discard_prompt(window, store, monkeypatch, app):
    window.title.setText("Không mất nháp")
    window.content.setPlainText("Nội dung chưa bấm lưu")
    with monkeypatch.context() as patch:
        patch.setattr(
            QMessageBox, "question", lambda *args: pytest.fail("Draft should be saved when closing")
        )
        window.close()
        assert window.stored_drafts()
        assert not store.posts()
    assert window.browser.wait(10000)
    app.processEvents()


def test_autosave_failure_keeps_window_open(window, store, monkeypatch):
    window.title.setText("Không được mất")
    window.content.setPlainText("Bản chưa lưu")
    with monkeypatch.context() as patch:
        patch.setattr(store, "set_preference", lambda *args: (_ for _ in ()).throw(OSError("disk full")))
        patch.setattr(QMessageBox, "warning", lambda *args: None)
        assert not window.autosave_draft()
        window.close()
        assert window.isVisible() and not window.closing
        assert "Chưa tự lưu" in window.autosave_note.text()


def test_new_unsaved_work_keeps_unrecovered_draft(window, store):
    first = {
        "one": {
            "post_id": None,
            "title": "Nháp cũ",
            "html": "<p>Cũ</p>",
            "plain": "Cũ",
            "tags": "",
            "images": [],
            "saved_at": "2026-11-16T00:00:00+00:00",
        }
    }
    store.set_preference("editor_drafts", json.dumps(first))
    window.title.setText("Nháp mới")
    window.content.setPlainText("Mới")
    window.autosave_draft()
    assert len(window.stored_drafts()) == 2
    window.save_post()
    assert list(window.stored_drafts()) == ["one"]


def test_row_selection_survives_refresh_and_no_link_disables_actions(window, store, task_data):
    for group in task_data[1]:
        store.create_job(task_data[0][0], group)
    view = window.post_manager
    view.refresh()
    view.table.setCurrentCell(1, 0)
    chosen = view.current_job_record()["id"]
    view.refresh()
    assert view.current_job_record()["id"] == chosen
    assert not view.open_button.isEnabled() and not view.copy_button.isEnabled()
    assert view.table.columnCount() == 6
    view.keyword.setText("không khớp")
    view.search()
    assert view.table.rowCount() == 0 and not view.export_button.isEnabled()


def test_sent_states_are_presented_without_approval_metadata(window, store, task_data):
    ids = [store.create_job(task_data[0][0], g) for g in task_data[1]]
    for job_id, status in zip(ids, ["submitted", "pending", "published"]):
        store.update_job(job_id, status=status, url=store.job(job_id)["group_url"] + "posts/123/")
    view = window.post_manager
    view.refresh()
    assert view.table.rowCount() == 3
    assert {view.table.item(i, 4).text() for i in range(3)} == {"Đã gửi"}


def test_quick_start_can_be_hidden_persistently(window, store):
    assert window.quick_start.isHidden()
    window.hide_quick_start()
    assert window.quick_start.isHidden() and store.preference("quick_start_done") == "1"


def test_edit_from_wizard_opens_chosen_post_and_respects_unsaved_work(window, store, task_data, monkeypatch):
    window.refresh_posts()
    first = next(
        window.post_list.item(i)
        for i in range(window.post_list.count())
        if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == task_data[0][1]
    )
    window.load_post(first)
    window.title.setText("Đang sửa bài khác")
    window.job_posts.setCurrentIndex(window.job_posts.findData(task_data[0][0]))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.edit_chosen_article()
    assert window.post_id == task_data[0][1] and window.dirty
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.edit_chosen_article()
    assert window.post_id == task_data[0][0] and not window.dirty
    assert "Lương 15 triệu" in window.content.toPlainText()


def test_draft_with_missing_image_does_not_replace_current_editor(window, store):
    store.set_preference(
        "editor_drafts",
        json.dumps(
            {
                "broken": {
                    "post_id": None,
                    "title": "Nháp lỗi",
                    "html": "<p>Nháp</p>",
                    "plain": "Nháp",
                    "tags": "",
                    "images": ["images/missing.png"],
                    "saved_at": "2026-11-17T00:00:00+00:00",
                }
            }
        ),
    )
    window.title.setText("Bài hiện tại")
    window.content.setPlainText("Giữ nguyên")
    with pytest.raises(ValueError, match="Không tìm thấy"):
        window.recover_draft()
    assert window.title.text() == "Bài hiện tại" and "broken" in window.stored_drafts()
