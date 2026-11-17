from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog


def test_editor_highlights_save_then_group_selection_and_keeps_review_required(window, store, monkeypatch):
    assert window.template_button.property("primary")
    assert not window.save_button.isEnabled() and not window.editor_post_button.isEnabled()
    window.title.setText("Tuyển kỹ sư")
    window.content.setPlainText("Nội dung cần tuyển")
    assert window.save_button.isEnabled() and window.save_button.property("primary")
    assert not window.editor_post_button.property("primary")
    window.save_button.click()
    assert store.post(window.post_id)["title"] == "Tuyển kỹ sư"
    assert not window.save_button.isEnabled() and window.editor_post_button.property("primary")
    assert window.autosave_note.text() == "Đã lưu bài"
    window.content.setPlainText("Nội dung đã chỉnh")
    assert window.save_button.property("primary") and not window.editor_post_button.property("primary")
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda *args: commands.append(args))
    window.editor_post_button.click()
    assert window.posting_steps.currentIndex() == 1 and window.tabs.currentIndex() == 2
    assert store.post(window.post_id)["plain"] == "Nội dung đã chỉnh"
    assert not commands and not store.batches()


def test_editor_button_updates_do_not_wait_for_webengine(window, monkeypatch):
    window.title.setText("Bài nháp")
    window.content.setHtml("<p>Nội dung</p>")

    def blocked(*args):
        raise AssertionError("Button state must not call JavaScript")

    monkeypatch.setattr(window.content, "evaluate", blocked)
    window.update_editor_actions()
    assert window.save_button.isEnabled()
    window.queue_active = True
    window.update_editor_actions()
    assert not window.editor_post_button.isEnabled() and window.save_button.isEnabled()
    window.queue_active = False


def test_editor_footer_fits_small_window_with_images_and_image_actions_work(window, store, task_data, app):
    window.refresh_posts()
    item = next(
        window.post_list.item(i)
        for i in range(window.post_list.count())
        if window.post_list.item(i).data(Qt.ItemDataRole.UserRole) == task_data[0][0]
    )
    window.load_post(item)
    other = store.post(task_data[0][1])["images"][0]
    window.add_image_item(other)
    window.images.setCurrentRow(1)
    window.image_up_action.trigger()
    assert window.images.item(0).data(Qt.ItemDataRole.UserRole) == other
    window.resize(980, 680)
    app.processEvents()
    assert window.width() == 980 and window.height() == 680
    for button in (window.save_button, window.editor_post_button, window.preview_button):
        point = button.mapTo(window, QPoint(0, button.height()))
        assert 0 < point.y() < window.height()
    assert window.images.isVisible() and "2" in window.image_count.text()


def test_group_form_validates_without_popup_and_saves_from_primary_button(window, store, monkeypatch):
    assert not window.group_save_button.isEnabled()
    window.group_name.setText("Nhóm kỹ thuật")
    window.group_url.setText("https://example.com/not-facebook")
    assert not window.group_save_button.isEnabled() and not window.group_validation.isHidden()
    window.group_url.setText("https://www.facebook.com/groups/123/")
    assert window.group_save_button.isEnabled() and window.group_save_button.property("primary")
    window.group_save_button.click()
    assert store.groups()[0]["name"] == "Nhóm kỹ thuật" and not window.group_save_button.isEnabled()
    assert window.delete_group_action.isEnabled()
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))
    window.group_open_button.click()
    assert opened == ["https://www.facebook.com/groups/123/"]


def test_support_exports_only_local_diagnostics(window, store, tmp_path, monkeypatch):
    assert not window.diagnostic_export_button.isEnabled()
    source = store.root / "link-diagnostics.json"
    source.write_text('[{"saved_link":false,"matched_create_requests":0}]')
    window.browser_done("open_group", {"message": "Đã mở nhóm"})
    assert window.diagnostic_export_button.isEnabled()
    target = tmp_path / "support.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(target), ""))
    monkeypatch.setattr(
        window.browser,
        "submit",
        lambda *args: (_ for _ in ()).throw(AssertionError("Export must stay local")),
    )
    window.diagnostic_export_button.click()
    assert target.read_bytes() == source.read_bytes()


def test_template_creation_has_one_primary_action_and_requires_main_fields(window):
    from facebook_helper.templates import RecruitmentDialog

    dialog = RecruitmentDialog(window)
    assert dialog.generate_button.property("primary") and not dialog.generate_button.isEnabled()
    dialog.fields["position"].setText("Kỹ sư")
    dialog.fields["company"].setText("Công ty")
    assert dialog.generate_button.isEnabled()
    dialog.generate_button.click()
    assert dialog.article and "KỸ SƯ" in dialog.article["title"]


def test_browser_worker_is_lazy_until_first_command(window, monkeypatch):
    assert not window.browser.isRunning()
    calls = []
    running = [False]

    def start():
        calls.append("start")
        running[0] = True

    monkeypatch.setattr(window.browser, "start", start)
    monkeypatch.setattr(window.browser, "isRunning", lambda: running[0])
    window.browser.submit("login")
    window.browser.submit("read_link", {"job_id": 1})
    assert calls == ["start"]
    assert window.browser.commands.get_nowait()[0] == "login"
    assert window.browser.commands.get_nowait()[0] == "read_link"
    running[0] = False
