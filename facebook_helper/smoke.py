"""Packaging check, explicitly invoked by CI; never touches a Facebook account."""

import json
import traceback

from PySide6.QtCore import QCoreApplication, QDate, QEvent, QMimeData, QTimer

from .ui import MainWindow


def run_smoke(app, store):
    from playwright.sync_api import sync_playwright

    result = {"ok": False}
    try:
        with sync_playwright() as playwright:
            with playwright.chromium.launch(headless=True) as browser:
                page = browser.new_page()
                page.set_content('<meta charset="utf-8"><h1>Facebook Helper · Kiểm tra đóng gói</h1>')
                assert page.locator("h1").inner_text() == "Facebook Helper · Kiểm tra đóng gói"
                page.screenshot(path=str(store.root / "packaged-browser.png"))
                result["chromium"] = browser.version
        window = MainWindow(store)
        window.show()
        app.processEvents()
        mime = QMimeData()
        mime.setHtml(
            '<p><b style="color:#2456ab">Kiểm tra dán định dạng</b></p><ol><li>PLC</li><li>Robot</li></ol>'
        )
        mime.setText("Kiểm tra dán định dạng\nPLC\nRobot")
        app.clipboard().setMimeData(mime)
        window.content.paste()
        assert window.content.evaluate("$.summernote.version") == "0.9.1"
        assert window.content.evaluate("!!document.querySelector('.note-toolbar')")
        assert "<b" in window.content.toHtml()
        assert "1. PLC" in window.content.toPlainText()
        window.copy_editor()
        assert app.clipboard().mimeData().hasHtml()
        result["rich_paste_and_copy"] = True
        assert window.posting_steps.count() == 4
        assert window.post_manager.table.columnCount() == 6
        assert window.post_manager.start.date() == window.post_manager.end.date() == QDate.currentDate()
        assert not window.history.isColumnHidden(5)
        assert window.result_group_button.text() == window.post_manager.group_button.text() == "Mở nhóm"
        assert window.editor_post_button.text() == "Chọn nhóm đăng"
        assert window.group_save_button.property("primary")
        assert window.settings_login_button.property("primary")
        result.update(today_filter=True, posting_link_column=True, group_actions=True, global_actions=True)
        window.mark_dirty()
        assert window.autosave_draft()
        assert window.stored_drafts() and not store.posts()
        result.update(guided_steps=4, result_columns=6, draft_saved=True)
        if app.platformName() == "offscreen":
            app.clipboard().clear()
        window.content.clear()
        window.dirty = False
        QTimer.singleShot(1000, window.close)
        code = app.exec()
        assert code == 0 and not window.browser.isRunning()
        tabs = window.tabs.count()
        window.content.release()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        result.update(ok=True, tabs=tabs, qt_started=True, worker_stopped=True)
        return 0
    except Exception:
        result["error"] = traceback.format_exc()
        return 1
    finally:
        (store.root / "smoke-result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
