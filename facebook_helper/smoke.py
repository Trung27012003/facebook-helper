"""Packaging check, explicitly invoked by CI; never touches a Facebook account."""

import json
import traceback

from PySide6.QtCore import QTimer

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
        QTimer.singleShot(1000, window.close)
        code = app.exec()
        assert code == 0 and not window.browser.isRunning()
        result.update(ok=True, tabs=window.tabs.count(), qt_started=True, worker_stopped=True)
        return 0
    except Exception:
        result["error"] = traceback.format_exc()
        return 1
    finally:
        (store.root / "smoke-result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
