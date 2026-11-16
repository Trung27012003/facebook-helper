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


def test_formatted_html_reaches_composer_via_native_clipboard_paste(page, store):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    fill_composer(
        page,
        "Tuyển kỹ sư\n• PLC\n• Robot",
        [],
        "<p><b>Tuyển kỹ sư</b></p><ul><li>PLC</li><li>Robot</li></ul>",
    )
    assert page.get_by_role("textbox").locator("b,strong").count() > 0
    assert page.get_by_role("textbox").locator("ul li").count() == 2
    assert not page.evaluate("window.submitted")


def test_platform_format_change_does_not_block_received_text(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").evaluate(
        "el=>el.addEventListener('paste',e=>{e.preventDefault();el.textContent=e.clipboardData.getData('text/plain')})"
    )
    fill_composer(page, "Tuyển kỹ sư", [], "<p><b>Tuyển kỹ sư</b></p>")
    assert page.get_by_role("textbox").inner_text() == "Tuyển kỹ sư"
    assert not page.evaluate("window.submitted")


def test_facebook_restriction_notice_stops_before_filling(page):
    page.set_content(COMPOSER + '<div role="alert">Bạn tạm thời bị chặn đăng bài</div>')
    with pytest.raises(ValueError, match="Facebook đang báo"):
        fill_composer(page, "Nội dung", [])
    assert page.get_by_role("textbox").inner_text() == ""


def test_removal_notice_after_click_stops_and_does_not_claim_published(page, store):
    html = PUBLISH_COMPOSER.replace(
        "window.submitted=true;",
        "window.submitted=true;const n=document.createElement('div');n.setAttribute('role','alert');n.innerText='Your post was removed';document.body.appendChild(n);",
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish", {"group_url": "https://www.facebook.com/groups/hr/", "body": "Nội dung", "images": []}
    )
    assert result["uncertain"] and not result["sent"]
    assert "removed" in result["message"]


def test_legacy_plain_only_history_is_not_silently_posted_again(store):
    worker = BrowserWorker(store.root)
    with pytest.raises(ValueError, match="Lượt đăng cũ chỉ có chữ thuần"):
        worker.execute("publish", {"body_html": "", "body": "Bài cũ"})


def test_equivalent_vietnamese_unicode_is_not_a_content_mismatch(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").evaluate("""el=>el.addEventListener('paste',e=>{e.preventDefault();
      el.innerHTML=e.clipboardData.getData('text/html');
      const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let node;
      while(node=walker.nextNode())node.textContent=node.textContent.normalize('NFD');
    })""")
    fill_composer(page, "Tuyển kỹ sư tự động hóa", [], "<p><b>Tuyển kỹ sư tự động hóa</b></p>")
    assert not page.evaluate("window.submitted")


def test_displayed_numbered_list_markers_do_not_create_false_mismatch(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role(
        "textbox"
    ).evaluate("""el=>el.addEventListener('paste',e=>{e.preventDefault();el.innerHTML=e.clipboardData.getData('text/html');
      el.querySelectorAll('ol li').forEach((li,i)=>li.prepend(String(i+1)+'. '));})""")
    fill_composer(page, "1. PLC\n2. Robot", [], "<ol><li>PLC</li><li>Robot</li></ol>")
    assert not page.evaluate("window.submitted")


def test_waits_for_delayed_paste_instead_of_reading_intermediate_placeholder(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role(
        "textbox"
    ).evaluate("""el=>el.addEventListener('paste',e=>{e.preventDefault();const html=e.clipboardData.getData('text/html');
      el.innerHTML='<span role="status">Đang cập nhật...</span>';setTimeout(()=>el.innerHTML=html,350);})""")
    fill_composer(page, "Nội dung đủ", [], "<p><b>Nội dung đủ</b></p>")
    assert page.get_by_role("textbox").inner_text() == "Nội dung đủ"


def test_readback_difference_no_longer_blocks_nonempty_composer(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").evaluate("""el=>el.addEventListener('paste',e=>{e.preventDefault();
      el.innerHTML=e.clipboardData.getData('text/html')+'<span>Thông tin bổ sung của giao diện</span>';})""")
    fill_composer(page, "Nội dung", [], "<p><b>Nội dung</b></p>")
    assert "Nội dung" in page.get_by_role("textbox").inner_text()
    assert not page.evaluate("window.submitted")


def test_photo_upload_after_paste_preserves_text_despite_noneditable_controls(page, store, task_data):
    html = (
        COMPOSER
        + """<script>document.querySelector('input').onchange=()=>{
      const el=document.querySelector('[role=textbox]');window.beforeUpload=el.innerText;
      const control=document.createElement('span');control.contentEditable='false';control.innerText='Xóa ảnh · đổi thứ tự';el.appendChild(control);
    };</script>"""
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    image = str(store.asset(store.post(task_data[0][0])["images"][0]))
    fill_composer(page, "Tuyển kỹ sư\n• PLC", [image], "<p><b>Tuyển kỹ sư</b></p><ul><li>PLC</li></ul>")
    assert "Tuyển kỹ sư" in page.evaluate("window.beforeUpload")
    assert not page.evaluate("window.submitted")
    assert page.locator("input").evaluate("el=>el.files.length") == 1


def test_editor_rerender_after_photo_upload_is_verified_again(page, store, task_data):
    html = (
        COMPOSER
        + """<script>document.querySelector('input').onchange=()=>{
      const old=document.querySelector('[role=textbox]'),replacement=old.cloneNode(true);old.replaceWith(replacement);
    };</script>"""
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    image = str(store.asset(store.post(task_data[0][0])["images"][0]))
    fill_composer(page, "Tuyển kỹ sư", [image], "<p><b>Tuyển kỹ sư</b></p>")
    assert page.get_by_role("textbox").inner_text() == "Tuyển kỹ sư"


def test_no_saved_text_comparison_is_performed(page):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    # The caller's plain/HTML representations can differ; only receipt is a gate now.
    fill_composer(page, "Bản chữ thuần dùng cho clipboard", [], "<p><b>Bản HTML có định dạng</b></p>")
    assert "Bản HTML có định dạng" in page.get_by_role("textbox").inner_text()


def test_empty_paste_stops_without_retry_or_posting(page, monkeypatch):
    from facebook_helper import composer

    monkeypatch.setattr(composer, "CONTENT_TIMEOUT", 0.5)
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").evaluate(
        """el=>el.addEventListener('paste',e=>{e.preventDefault();window.pastes=(window.pastes||0)+1;})"""
    )
    with pytest.raises(ValueError, match="chưa nhận được phần chữ"):
        fill_composer(page, "Nội dung", [], "<p>Nội dung</p>")
    assert page.evaluate("window.pastes") == 1
    assert not page.evaluate("window.submitted")


def test_long_post_with_images_reaches_post_button_despite_readback_difference(page, store, task_data):
    long_body = "\n".join(
        f"Dòng {i}: Tuyển kỹ sư tự động hóa PLC, HMI, Robot và cơ hội phát triển." for i in range(240)
    )
    markup = "<p><b>TUYỂN DỤNG</b></p>" + "".join("<p>" + line + "</p>" for line in long_body.splitlines())
    html = (
        PUBLISH_COMPOSER
        + """<script>
      window.readyImages=false;window.pasteCount=0;
      const editor=document.querySelector('[role=textbox]');
      editor.addEventListener('paste',e=>{e.preventDefault();window.pasteCount++;
        editor.innerHTML=e.clipboardData.getData('text/html')+'<span contenteditable="false">Chữ bổ sung của giao diện ảnh</span>';});
      document.querySelector('input').onchange=()=>{document.querySelector('button').disabled=true;
        const progress=document.createElement('div');progress.setAttribute('role','progressbar');progress.style.height='10px';progress.style.width='100px';document.querySelector('[role=dialog]').appendChild(progress);
        setTimeout(()=>{window.readyImages=true;progress.remove();document.querySelector('button').disabled=false},500);};
      document.querySelector('button').addEventListener('click',()=>window.uploadDoneAtPost=window.readyImages);
    </script>"""
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    images = [str(store.asset(store.post(post)["images"][0])) for post in task_data[0]]
    result = worker.execute(
        "publish",
        {
            "group_url": "https://www.facebook.com/groups/hr/",
            "body": long_body,
            "body_html": markup,
            "images": images,
        },
    )
    assert result["sent"] and page.evaluate("window.submitted")
    assert page.evaluate("window.uploadDoneAtPost") and page.evaluate("window.pasteCount") == 1
    assert long_body.splitlines()[-1] in page.evaluate("window.savedText")


def test_upload_timeout_prevents_submission(page, store, task_data, monkeypatch):
    from facebook_helper import composer

    monkeypatch.setattr(composer, "UPLOAD_TIMEOUT", 0.6)
    html = (
        COMPOSER
        + """<script>document.querySelector('input').onchange=()=>{const p=document.createElement('div');p.setAttribute('role','progressbar');p.style.height='10px';p.style.width='100px';document.querySelector('[role=dialog]').appendChild(p);};</script>"""
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    image = str(store.asset(store.post(task_data[0][0])["images"][0]))
    with pytest.raises(ValueError, match="Ảnh vẫn đang tải"):
        fill_composer(page, "Bài viết", [image], "<p>Bài viết</p>")
    assert not page.evaluate("window.submitted")


def test_existing_open_draft_can_be_published_without_pasting_again(page, store):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=PUBLISH_COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").fill("Bản đã có đủ chữ và ảnh do người dùng kiểm tra")
    page.get_by_role("textbox").evaluate("el=>el.addEventListener('paste',()=>{window.unexpectedPaste=true})")
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish_current",
        {"group_url": "https://www.facebook.com/groups/hr/", "body": "Không dán phần này", "images": []},
    )
    assert result["sent"] and page.evaluate("window.submitted")
    assert page.evaluate("window.savedText") == "Bản đã có đủ chữ và ảnh do người dùng kiểm tra"
    assert not page.evaluate("window.unexpectedPaste||false")


def test_publish_open_draft_rejects_wrong_group(page, store):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=PUBLISH_COMPOSER),
    )
    page.goto("https://www.facebook.com/groups/other/")
    worker = BrowserWorker(store.root)
    worker.page = page
    with pytest.raises(ValueError, match="không ở đúng nhóm"):
        worker.execute("publish_current", {"group_url": "https://www.facebook.com/groups/hr/"})
    assert not page.evaluate("window.submitted")


def test_completed_progress_indicator_does_not_block_posting(page, store):
    html = PUBLISH_COMPOSER.replace(
        "</div><script>",
        '<div role="progressbar" aria-valuenow="100" aria-valuemax="100" style="height:10px">Đã tải xong</div></div><script>',
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    page.goto("https://www.facebook.com/groups/hr/")
    page.get_by_role("textbox").fill("Bài đã sẵn sàng")
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute("publish_current", {"group_url": "https://www.facebook.com/groups/hr/"})
    assert result["sent"] and page.evaluate("window.submitted")


def test_new_visible_post_gets_published_status_and_permalink(page, store):
    html = PUBLISH_COMPOSER.replace(
        "window.submitted=true;",
        "window.submitted=true;const a=document.createElement('article');a.setAttribute('role','article');a.innerHTML='<p>Tuyển kỹ sư mới</p><a href=https://www.facebook.com/groups/hr/posts/777/>Vừa xong</a>';document.body.appendChild(a);",
    )
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    worker = BrowserWorker(store.root)
    worker.page = page
    result = worker.execute(
        "publish",
        {"group_url": "https://www.facebook.com/groups/hr/", "body": "Tuyển kỹ sư mới", "images": []},
    )
    assert result["status"] == "published"
    assert result["url"].endswith("/posts/777/")
