"""Playwright lives entirely on one worker thread. No automatic final submission."""

import queue
import re
import uuid
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .domain import normalize_group, post_url


class BrowserWorker(QThread):
    done = Signal(str, object)
    failed = Signal(str, str, object)
    progress = Signal(str)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.commands = queue.Queue()
        self.context = None
        self.page = None

    def submit(self, action, payload=None):
        self.commands.put((action, payload or {}))

    def run(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            while True:
                try:
                    action, payload = self.commands.get(timeout=0.1)
                except queue.Empty:
                    if self.context:
                        try:
                            self.context.pages[0].wait_for_timeout(50)
                        except Exception:
                            pass
                    continue
                if action == "stop":
                    break
                try:
                    self.progress.emit("Đang xử lý trình duyệt…")
                    if self.context is None or not self.context.pages:
                        if self.context:
                            try:
                                self.context.close()
                            except Exception:
                                pass
                        self.context = playwright.chromium.launch_persistent_context(
                            str(self.root / "browser"),
                            headless=False,
                            viewport={"width": 1280, "height": 900},
                            locale="vi-VN",
                            accept_downloads=False,
                        )
                        self.context.set_default_timeout(6000)
                        self.context.set_default_navigation_timeout(30000)
                        self.page = self.context.pages[0]
                    if self.page.is_closed():
                        self.page = self.context.new_page()
                    result = self.execute(action, payload)
                    self.done.emit(action, result)
                except Exception as exc:
                    message = str(exc)
                    if "Executable doesn't exist" in message:
                        message = "Thiếu Chromium. Chạy: python -m playwright install chromium"
                    self.failed.emit(action, message[:1200], payload)
                finally:
                    self.progress.emit("")
            if self.context:
                try:
                    self.context.close()
                except Exception:
                    pass

    def execute(self, action, payload):
        if action == "login":
            self.page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            self.page.bring_to_front()
            return {"message": "Đăng nhập trực tiếp trong trình duyệt. Sau đó quay lại ứng dụng."}
        if action == "open_group":
            self.page.goto(normalize_group(payload["group_url"]), wait_until="domcontentloaded")
            self.page.bring_to_front()
            return {**payload, "message": "Đã mở nhóm. Hãy mở ô tạo bài trên Facebook, rồi bấm Điền bài."}
        if action == "fill":
            if normalize_group(self.page.url) != normalize_group(payload["group_url"]):
                raise ValueError("Trình duyệt chưa ở đúng nhóm. Bấm Mở nhóm trước.")
            fill_composer(self.page, payload["body"], payload["images"])
            self.page.bring_to_front()
            return {
                **payload,
                "message": "Đã điền nội dung và đính kèm ảnh. Kiểm tra trên Facebook rồi tự bấm Đăng.",
            }
        if action == "read_link":
            url = post_url(self.page.url, payload["group_url"])
            return {**payload, "url": url, "message": "Đã lấy link bài đang mở. Bạn có thể bấm Copy link."}
        if action == "capture":
            # Navigate to one validated permalink rather than accidentally capturing the group feed.
            url = post_url(payload["url"], payload["group_url"])
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.bring_to_front()
            return {
                **payload,
                "message": "Đã mở link bài. Kiểm tra bài và cuộn đến vị trí cần chụp, rồi bấm Chụp màn hình.",
            }
        if action == "screenshot":
            url = post_url(self.page.url, payload["group_url"])
            expected = post_url(payload["url"], payload["group_url"])
            if url != expected:
                raise ValueError("Trang hiện tại khác link bài đã lưu. Mở lại link bài trước khi chụp.")
            evidence = f"evidence/{payload['job_id']}-{uuid.uuid4().hex}.png"
            self.page.screenshot(path=str(self.root / evidence), full_page=False)
            return {
                **payload,
                "url": url,
                "evidence": evidence,
                "message": "Đã lưu ảnh vùng đang hiển thị. Ảnh chụp không tự xác nhận bài đã được duyệt.",
            }
        raise ValueError("Thao tác trình duyệt không hợp lệ.")


def fill_composer(page, body, images):
    """Require an already opened, unambiguous composer; never click the Post button."""
    dialogs = page.get_by_role("dialog").filter(has=page.locator('[role="textbox"][contenteditable="true"]'))
    if dialogs.count() != 1:
        raise ValueError("Hãy mở cửa sổ Tạo bài viết trên Facebook và đóng các cửa sổ soạn khác.")
    dialog = dialogs.first
    editors = dialog.locator('[role="textbox"][contenteditable="true"]')
    if editors.count() != 1:
        raise ValueError("Không xác định được ô nội dung. Bạn có thể dùng nút Sao chép để dán thủ công.")
    if editors.first.inner_text().strip():
        raise ValueError("Ô Facebook đang có nội dung. Xóa nội dung cũ hoặc dán thủ công để tránh ghi đè.")
    # Validate image access before changing anything in the composer.
    for path in images:
        if not Path(path).is_file():
            raise ValueError(f"Ảnh không tồn tại: {Path(path).name}")
    if images:
        inputs = dialog.locator('input[type="file"][accept*="image"]')
        if inputs.count() != 1:
            buttons = dialog.get_by_role("button", name=re.compile(r"^(Ảnh/video|Photo/video)$", re.I))
            if buttons.count() == 1:
                buttons.click()
            inputs = dialog.locator('input[type="file"][accept*="image"]')
        if inputs.count() != 1:
            raise ValueError("Chưa thấy ô tải ảnh. Mở mục Ảnh/video trong cửa sổ soạn bài rồi thử lại.")
        if len(images) > 1 and inputs.first.get_attribute("multiple") is None:
            raise ValueError("Ô tải ảnh hiện tại không hỗ trợ nhiều ảnh. Hãy thêm ảnh thủ công.")
        inputs.first.set_input_files(images)
    editors.first.fill(body)
