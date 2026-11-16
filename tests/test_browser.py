import pytest
from playwright.sync_api import sync_playwright
from PySide6.QtGui import QColor, QImage

from facebook_helper.browser import BrowserWorker, fill_composer


@pytest.fixture
def page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


COMPOSER = """
<div role="dialog">
 <div role="textbox" contenteditable="true"></div>
 <input type="file" accept="image/*" multiple>
 <button onclick="window.submitted=true">Đăng</button>
</div>
<script>window.submitted=false;</script>
"""


def test_fill_unicode_multiple_images_without_submit(page, tmp_path, app):
    images = []
    for index in range(2):
        image = QImage(8, 8, QImage.Format.Format_RGB32)
        image.fill(QColor("blue"))
        target = tmp_path / f"{index}.png"
        image.save(str(target))
        images.append(str(target))
    page.set_content(COMPOSER)
    fill_composer(page, "Tuyển kế toán\nLương 15 triệu\n#tuyendung", images)
    assert page.get_by_role("textbox").inner_text() == "Tuyển kế toán\nLương 15 triệu\n#tuyendung"
    assert page.locator('input[type="file"]').evaluate("node => node.files.length") == 2
    assert page.evaluate("window.submitted") is False


def test_refuse_overwrite_existing_draft(page):
    page.set_content(COMPOSER)
    page.get_by_role("textbox").fill("Bài đang soạn")
    with pytest.raises(ValueError, match="đang có nội dung"):
        fill_composer(page, "Bài mới", [])
    assert page.get_by_role("textbox").inner_text() == "Bài đang soạn"
    assert page.evaluate("window.submitted") is False


def test_refuse_ambiguous_dialogs(page):
    page.set_content(COMPOSER + COMPOSER)
    with pytest.raises(ValueError, match="Tạo bài viết"):
        fill_composer(page, "Nội dung", [])


def test_refuse_missing_attachment_without_changing_text(page, tmp_path):
    page.set_content(COMPOSER)
    with pytest.raises(ValueError, match="không tồn tại"):
        fill_composer(page, "Nội dung", [str(tmp_path / "missing.png")])
    assert page.get_by_role("textbox").inner_text() == ""


def test_capture_refuses_other_post_and_writes_viewport(page, store, job):
    worker = BrowserWorker(store.root)
    worker.page = page
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html", body="<h1>Tin tuyển dụng mô phỏng</h1>"),
    )
    url = "https://www.facebook.com/groups/hr-hanoi/posts/123/"
    page.goto(url)
    payload = {"job_id": job, "url": url, "group_url": "https://www.facebook.com/groups/hr-hanoi/"}
    assert worker.execute("read_link", payload)["url"] == url
    result = worker.execute("screenshot", payload)
    assert store.asset(result["evidence"]).stat().st_size > 0
    assert store.job(job)["status"] == "draft"
    page.goto("https://www.facebook.com/groups/hr-hanoi/posts/456/")
    with pytest.raises(ValueError, match="khác link"):
        worker.execute("screenshot", payload)
