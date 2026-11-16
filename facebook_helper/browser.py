"""Playwright lives entirely on one worker thread. No automatic final submission."""

import queue
import re
import uuid
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .composer import canonical_text, wait_for_composer
from .domain import normalize_group, post_url
from .formatting import facebook_html


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
        if action in {"fill", "prepare", "publish"} and payload.get("body_html") == "":
            raise ValueError(
                "Lượt đăng cũ chỉ có chữ thuần. Hãy lưu lại bài bằng Summernote rồi tạo danh sách đăng mới để dùng định dạng; không tự đăng bản chữ thường."
            )
        if action == "login":
            self.page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            self.page.bring_to_front()
            return {"message": "Đăng nhập trực tiếp trong trình duyệt. Sau đó quay lại ứng dụng."}
        if action == "open_group":
            self.page.goto(normalize_group(payload["group_url"]), wait_until="domcontentloaded")
            self.page.bring_to_front()
            return {**payload, "message": "Đã mở nhóm. Hãy mở ô tạo bài trên Facebook, rồi bấm Điền bài."}
        if action == "fill":
            check_platform_notice(self.page)
            if normalize_group(self.page.url) != normalize_group(payload["group_url"]):
                raise ValueError("Trình duyệt chưa ở đúng nhóm. Bấm Mở nhóm trước.")
            fill_composer(self.page, payload["body"], payload["images"], payload.get("body_html"))
            self.page.bring_to_front()
            return {
                **payload,
                "message": "Đã điền nội dung và đính kèm ảnh. Kiểm tra trên Facebook rồi tự bấm Đăng.",
            }
        if action in {"prepare", "publish"}:
            self.page.goto(normalize_group(payload["group_url"]), wait_until="domcontentloaded")
            self.page.bring_to_front()
            check_platform_notice(self.page)
            if normalize_group(self.page.url) != normalize_group(payload["group_url"]):
                raise ValueError(
                    "Chưa vào được đúng nhóm. Hãy đăng nhập Facebook và kiểm tra quyền vào nhóm."
                )
            if not open_composer(self.page):
                return {
                    **payload,
                    "filled": False,
                    "sent": False,
                    "needs_composer": True,
                    "message": "Đã mở nhóm. Hãy bấm Viết gì đó/Tạo bài viết trên Facebook, rồi bấm Điền bài trong ứng dụng. Danh sách đã tạm dừng.",
                }
            fill_composer(self.page, payload["body"], payload["images"], payload.get("body_html"))
            if action == "prepare":
                return {
                    **payload,
                    "filled": True,
                    "message": "Đã chuẩn bị bài. Kiểm tra trên Facebook, bấm Đăng rồi chọn Đã gửi · sang nhóm sau.",
                }
            dialog = self.page.get_by_role("dialog").filter(
                has=self.page.locator('[role="textbox"][contenteditable="true"]')
            )
            submit = dialog.get_by_role("button", name=re.compile(r"^(Đăng|Post)$", re.I))
            if submit.count() != 1:
                raise ValueError(
                    "Không xác định được nút Đăng. Danh sách đã dừng; hãy kiểm tra và đăng bằng tay."
                )
            # Readiness must be established before clicking, so a failed readiness check is retryable.
            from playwright.sync_api import expect

            expect(submit).to_be_enabled(timeout=30000)
            check_platform_notice(self.page)
            payload["submission_started"] = True
            try:
                submit.click(timeout=10000)
                dialog.wait_for(state="hidden", timeout=20000)
                self.page.wait_for_timeout(1500)
                check_platform_notice(self.page)
            except Exception as exc:
                return {
                    **payload,
                    "filled": True,
                    "sent": False,
                    "uncertain": True,
                    "message": "Đã thử bấm Đăng nhưng chưa xác định được kết quả. Kiểm tra Facebook trước khi thử lại để tránh gửi trùng. Danh sách đã tạm dừng. "
                    + str(exc)[:600],
                }
            return {
                **payload,
                "filled": True,
                "sent": True,
                "message": "Đã bấm Đăng. Danh sách đã tạm dừng: kiểm tra bài còn hiển thị hoặc chờ duyệt trước khi chuyển nhóm.",
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


def fill_composer(page, body, images, html=None):
    """Require an already opened, unambiguous composer; never click the Post button."""
    check_platform_notice(page)
    dialogs = page.get_by_role("dialog").filter(has=page.locator('[role="textbox"][contenteditable="true"]'))
    if dialogs.count() != 1:
        raise ValueError("Hãy mở cửa sổ Tạo bài viết trên Facebook và đóng các cửa sổ soạn khác.")
    dialog = dialogs.first
    editors = dialog.locator('[role="textbox"][contenteditable="true"]')
    if editors.count() != 1:
        raise ValueError("Không xác định được ô nội dung. Bạn có thể dùng nút Sao chép để dán thủ công.")
    if canonical_text(editors.first.inner_text()):
        raise ValueError("Ô Facebook đang có nội dung. Xóa nội dung cũ hoặc dán thủ công để tránh ghi đè.")
    # Validate image access before changing anything in the composer.
    for path in images:
        if not Path(path).is_file():
            raise ValueError(f"Ảnh không tồn tại: {Path(path).name}")
    image_input = None
    if images:
        inputs = dialog.locator('input[type="file"][accept*="image"]')
        if inputs.count() != 1:
            buttons = dialog.get_by_role("button", name="Ảnh/video", exact=True).or_(
                dialog.get_by_role("button", name="Photo/video", exact=True)
            )
            if buttons.count() == 1:
                buttons.click()
            inputs = dialog.locator('input[type="file"][accept*="image"]')
        if inputs.count() != 1:
            raise ValueError("Chưa thấy ô tải ảnh. Mở mục Ảnh/video trong cửa sổ soạn bài rồi thử lại.")
        if len(images) > 1 and inputs.first.get_attribute("multiple") is None:
            raise ValueError("Ô tải ảnh hiện tại không hỗ trợ nhiều ảnh. Hãy thêm ảnh thủ công.")
        image_input = inputs.first
    check_platform_notice(page)
    if html:
        markup = facebook_html(html)
        try:
            origin = "https://" + page.url.split("/")[2]
            page.context.grant_permissions(["clipboard-write"], origin=origin)
            page.bring_to_front()
            editors.first.click()
            page.evaluate(
                """async ({html,text}) => {
                await navigator.clipboard.write([new ClipboardItem({
                  'text/html': new Blob([html], {type:'text/html'}),
                  'text/plain': new Blob([text], {type:'text/plain'})
                })]);
            }""",
                {"html": markup, "text": body},
            )
            editors.first.click()
            editors.first.press("ControlOrMeta+V")
            from playwright.sync_api import expect

            expect(editors.first).not_to_be_empty(timeout=5000)
        except Exception as exc:
            raise ValueError(
                "Chưa dán được định dạng vào Facebook. Danh sách đã dừng; dùng Sao chép bài có định dạng rồi Ctrl+V trong ô Facebook. Không tự chuyển sang chữ thuần."
            ) from exc
        wait_for_composer(page, dialog, body, markup)
    else:
        editors.first.fill(body)
        wait_for_composer(page, dialog, body)
    if image_input is not None:
        image_input.set_input_files(images)
        wait_for_composer(page, dialog, body, markup if html else None)


def open_composer(page):
    """Only click one recognizable group composer opener; otherwise request manual help."""
    dialogs = page.get_by_role("dialog").filter(has=page.locator('[role="textbox"][contenteditable="true"]'))
    if dialogs.count() == 1:
        return True
    if dialogs.count() > 1:
        raise ValueError("Đang có nhiều cửa sổ soạn bài. Hãy đóng bớt trước khi tiếp tục.")
    labels = re.compile(
        r"^(Viết gì đó.*|Bạn viết gì đi.*|Bạn đang nghĩ gì.*|Write something.*|Create a post|Tạo bài viết)$",
        re.I,
    )
    opener = page.get_by_role("button", name=labels)
    if opener.count() == 0:
        try:
            opener.first.wait_for(state="visible", timeout=8000)
        except Exception:
            return False
    if opener.count() != 1:
        return False
    opener.click()
    try:
        dialogs.wait_for(state="visible", timeout=8000)
    except Exception:
        return False
    return True


def check_platform_notice(page):
    if re.search(r"/(?:checkpoint|challenge|login)(?:/|\?|$)", page.url):
        raise ValueError("Facebook yêu cầu đăng nhập/xác thực. Đã dừng; hãy xử lý trực tiếp trên Facebook.")
    pattern = re.compile(
        r"temporarily blocked|we limit how often|automated behavio|couldn.t post|post.{0,60}(?:removed|deleted)|tạm thời bị chặn|hạn chế.{0,40}đăng|không thể đăng|bài viết.{0,60}(?:bị xóa|đã bị gỡ|đã bị xóa)",
        re.I,
    )
    for notice in page.locator('[role="alert"], [role="alertdialog"], [role="status"]').all():
        if notice.is_visible():
            text = notice.inner_text()
            if pattern.search(text):
                raise ValueError(
                    "Facebook đang báo: "
                    + text[:600]
                    + "\nĐã dừng, không gửi lại hoặc chuyển nhóm tự động. Hãy kiểm tra thông báo và quy định nhóm."
                )
