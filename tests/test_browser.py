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


def test_two_different_posts_fill_their_own_groups_sequentially(page, store, task_data):
    import json

    page.route(
        "https://www.facebook.com/**", lambda route: route.fulfill(content_type="text/html", body=COMPOSER)
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    posts, groups = task_data
    for post_id, group_id in zip(posts, groups):
        job = store.job(store.create_job(post_id, group_id))
        payload = {
            **job,
            "job_id": job["id"],
            "images": [str(store.asset(image)) for image in json.loads(job["images"])],
        }
        worker.execute("open_group", payload)
        result = worker.execute("fill", payload)
        assert result["job_id"] == job["id"]
        # Chromium innerText adds a newline for an empty block; selected text matches copy/paste.
        actual = page.get_by_role("textbox").evaluate("""node => {
            const range = document.createRange(); range.selectNodeContents(node);
            const selection = window.getSelection();
            selection.removeAllRanges(); selection.addRange(range);
            return selection.toString();
        }""")
        assert actual == job["body"]
        assert page.locator('input[type="file"]').evaluate("node => node.files[0].name") == (
            store.asset(json.loads(job["images"])[0]).name
        )
        assert page.evaluate("window.submitted") is False


def test_fill_rejects_wrong_group_before_modifying_composer(page, store):
    page.route(
        "https://www.facebook.com/**", lambda route: route.fulfill(content_type="text/html", body=COMPOSER)
    )
    page.goto("https://www.facebook.com/groups/hr-1/")
    worker = BrowserWorker(store.root)
    worker.page = page
    with pytest.raises(ValueError, match="chưa ở đúng nhóm"):
        worker.execute(
            "fill", {"group_url": "https://facebook.com/groups/hr-0/", "body": "Sai nhóm", "images": []}
        )
    assert page.get_by_role("textbox").inner_text() == ""
    assert page.evaluate("window.submitted") is False


@pytest.mark.parametrize(
    "body",
    [
        "<p>Không có cửa sổ tạo bài</p>",
        '<div role="dialog"><div role="textbox" contenteditable="true"></div>'
        '<div role="textbox" contenteditable="true"></div></div>',
    ],
)
def test_missing_or_ambiguous_composer_is_rejected(page, body):
    page.set_content(body)
    with pytest.raises(ValueError):
        fill_composer(page, "Nội dung", [])


@pytest.mark.parametrize(
    "url", ["https://www.facebook.com/groups/hr-hanoi/", "https://www.facebook.com/groups/other/posts/101/"]
)
def test_read_link_rejects_feed_or_different_group(page, store, url):
    page.route("https://www.facebook.com/**", lambda route: route.fulfill(body="mock"))
    page.goto(url)
    worker = BrowserWorker(store.root)
    worker.page = page
    with pytest.raises(ValueError):
        worker.execute("read_link", {"group_url": "https://www.facebook.com/groups/hr-hanoi/"})


def test_multiple_attachments_reject_single_file_input_without_modification(page, store, task_data):
    page.set_content(COMPOSER.replace(" multiple", ""))
    paths = [str(store.asset(store.post(post_id)["images"][0])) for post_id in task_data[0]]
    with pytest.raises(ValueError, match="không hỗ trợ nhiều ảnh"):
        fill_composer(page, "Nội dung", paths)
    assert page.get_by_role("textbox").inner_text() == ""
    assert page.locator('input[type="file"]').evaluate("node => node.files.length") == 0


@pytest.mark.parametrize("label", ["Ảnh/video", "Photo/video"])
def test_photo_button_fallback_uploads_images_in_selected_order(page, store, task_data, label):
    from pathlib import Path

    page.set_content(
        """<div role="dialog"><div role="textbox" contenteditable="true"></div>
    <button onclick="this.outerHTML='<input type=file accept=image/* multiple>'">PHOTO_BUTTON</button>
    <button onclick="window.submitted=true">Đăng</button></div><script>window.submitted=false</script>""".replace(
            "PHOTO_BUTTON", label
        )
    )
    paths = [str(store.asset(store.post(post_id)["images"][0])) for post_id in reversed(task_data[0])]
    fill_composer(page, "Giữ thứ tự ảnh", paths)
    assert page.locator('input[type="file"]').evaluate(
        "node => Array.from(node.files, file => file.name)"
    ) == [Path(path).name for path in paths]
    assert page.evaluate("window.submitted") is False


PUBLISH_COMPOSER = """<div role="dialog">
<div role="textbox" contenteditable="true"></div><input type="file" accept="image/*" multiple>
<button onclick="window.savedText=document.querySelector('[role=textbox]').innerText;
window.submitted=true;this.closest('[role=dialog]').remove();">Đăng</button>
</div><script>window.submitted=false;</script>"""


def test_prepare_opens_composer_and_keeps_final_submission_manual(page, store):
    html = (
        """<button onclick="document.getElementById('slot').innerHTML=document.getElementById('form').innerHTML">Viết gì đó...</button>
    <main id="slot"></main><template id="form">"""
        + PUBLISH_COMPOSER
        + """</template><script>window.submitted=false;</script>"""
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "prepare", {"group_url": "https://facebook.com/groups/hr/", "body": "Tuyển kỹ sư", "images": []}
    )
    assert result["filled"]
    assert page.get_by_role("textbox").inner_text() == "Tuyển kỹ sư"
    assert page.evaluate("window.submitted") is False


def test_explicit_publish_clicks_post_after_filling_and_records_submission_attempt(page, store):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=PUBLISH_COMPOSER),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish", {"group_url": "https://facebook.com/groups/hr/", "body": "Tuyển kế toán", "images": []}
    )
    assert result["filled"] and result["sent"] and result["submission_started"]
    assert page.evaluate("window.savedText") == "Tuyển kế toán"
    assert page.evaluate("window.submitted") is True
    assert not result.get("uncertain")


def test_publish_does_not_guess_when_composer_opener_is_missing(page, store):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html", body="<p>Group</p>"),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish", {"group_url": "https://facebook.com/groups/hr/", "body": "Tuyển", "images": []}
    )
    assert result["needs_composer"] and not result["sent"]
    assert not result.get("submission_started")


def test_publish_never_retries_when_post_click_outcome_is_unknown(page, store, monkeypatch):
    from playwright.sync_api import Locator

    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=PUBLISH_COMPOSER),
    )
    original = Locator.wait_for

    def wait(locator, *args, **kwargs):
        if kwargs.get("state") == "hidden":
            raise TimeoutError("confirmation lost after clicking Post")
        return original(locator, *args, **kwargs)

    monkeypatch.setattr(Locator, "wait_for", wait)
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish", {"group_url": "https://facebook.com/groups/hr/", "body": "Tuyển", "images": []}
    )
    assert result["uncertain"] and not result["sent"] and result["submission_started"]
    assert page.evaluate("window.submitted") is True
