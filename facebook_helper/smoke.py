"""Packaging check, explicitly invoked by CI; never touches a Facebook account."""

import json
import traceback

from PySide6.QtCore import QCoreApplication, QEvent, QMimeData, QTimer
from PySide6.QtGui import QFont, QTextCursor

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
        cursor = QTextCursor(window.content.document())
        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
        assert cursor.charFormat().fontWeight() == QFont.Weight.Bold
        assert cursor.charFormat().foreground().color().name() == "#2456ab"
        assert "1. PLC" in window.content.toPlainText()
        window.copy_editor()
        assert app.clipboard().mimeData().hasHtml()
        result["rich_paste_and_copy"] = True
        if app.platformName() == "offscreen":
            app.clipboard().clear()
        window.content.clear()
        window.dirty = False
        QTimer.singleShot(1000, window.close)
        code = app.exec()
        assert code == 0 and not window.browser.isRunning()
        tabs = window.tabs.count()
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
