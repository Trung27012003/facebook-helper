import pytest
from playwright.sync_api import sync_playwright
from PySide6.QtCore import QDate

from facebook_helper.browser import BrowserWorker
from facebook_helper.monitoring import inspect_page
from facebook_helper.storage import Store

GROUP = "https://www.facebook.com/groups/hr-hanoi/"
LINK = GROUP + "posts/123/"
BODY = "Tuyển kỹ sư PLC. Lương 25 triệu."
SENT_AT = "2026-11-17T03:00:00+00:00"


@pytest.fixture
def page():
    with sync_playwright() as p:
        with p.chromium.launch() as b:
            context = b.new_context()
            page = context.new_page()
            yield page


def prepare(page, html, path=GROUP):
    page.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html),
    )
    page.goto(path)


def payload(**kw):
    return {"body": BODY, "group_url": GROUP, "url": LINK, "sent_at": SENT_AT, **kw}


def card(label="", link=LINK, when=SENT_AT):
    return f'<article role="article"><p>{BODY}</p><time datetime="{when}"></time><a href="{link}">17/11</a>{label}</article>'


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Chờ duyệt", "pending"),
        ("Pending approval", "pending"),
        ("Bài viết đã bị từ chối", "rejected"),
        ("Bài viết đã bị gỡ", "removed"),
        ("Đã được phê duyệt", "published"),
        ("Published", "published"),
    ],
)
def test_reads_status_only_from_matched_post(page, label, expected):
    prepare(page, card(f'<div role="status">{label}</div>'), LINK)
    assert inspect_page(page, payload())["outcome"] == expected


def test_known_post_in_group_feed_is_visible_but_permalink_alone_is_not_approval(page):
    prepare(page, card())
    assert inspect_page(page, payload())["outcome"] == "published"
    page.goto(LINK)
    assert inspect_page(page, payload())["outcome"] == "unknown"


def test_pending_card_in_feed_never_becomes_published(page):
    prepare(page, card("<div>Chờ quản trị viên phê duyệt</div>"))
    assert inspect_page(page, payload())["outcome"] == "pending"


@pytest.mark.parametrize(
    "html",
    [
        '<div role="alert">Chờ duyệt</div>',
        card(link=GROUP + "posts/999/"),
        card() + card(),
        '<div role="dialog">' + card() + "</div>",
    ],
)
def test_missing_wrong_link_ambiguous_or_modal_stays_unknown(page, html):
    prepare(page, html)
    assert inspect_page(page, payload())["outcome"] == "unknown"


def test_without_link_requires_own_content_and_matching_send_timestamp(page):
    prepare(page, '<div role="tab" aria-selected="true">Pending</div>' + card(), GROUP + "your_content/")
    assert inspect_page(page, payload(url=""), own_content=True)["outcome"] == "pending"
    assert inspect_page(page, payload(url=""))["outcome"] == "unknown"
    assert (
        inspect_page(page, payload(url="", sent_at="2026-11-10T03:00:00+00:00"), own_content=True)["outcome"]
        == "unknown"
    )
    assert inspect_page(page, payload(url="", sent_at=""), own_content=True)["outcome"] == "unknown"


def test_content_words_are_not_status_metadata(page):
    text = "Đã được phê duyệt hồ sơ ứng viên. Chờ duyệt ngân sách."
    prepare(page, f'<article role="article">{text}<a href="{LINK}">Link</a></article>', LINK)
    assert inspect_page(page, payload(body=text))["outcome"] == "unknown"


@pytest.mark.parametrize("status,expected", [("Chờ duyệt", "pending"), ("Bài viết đã bị gỡ", "removed")])
def test_worker_checks_in_separate_tab_without_posting_or_changing_current_page(
    page, tmp_path, status, expected
):
    page.context.route(
        "https://www.facebook.com/**",
        lambda route: route.fulfill(
            content_type="text/html; charset=utf-8", body=card(f'<div role="status">{status}</div>')
        ),
    )
    page.goto(GROUP)
    page.set_content('<div role="textbox" contenteditable="true">Bản đang soạn</div>')
    worker = BrowserWorker(tmp_path)
    worker.page = page
    worker.context = page.context
    result = worker.execute("check_status", payload())
    assert result["outcome"] == expected
    assert page.get_by_role("textbox").inner_text() == "Bản đang soạn"
    assert len(page.context.pages) == 1


def test_worker_discovers_own_content_tab_when_post_has_no_link(page, tmp_path):
    def route(r):
        html = (
            '<a href="' + GROUP + 'your_content/">Quản lý bài viết</a>'
            if r.request.url.rstrip("/") == GROUP.rstrip("/")
            else '<div role="tab" aria-selected="true">Pending</div>' + card()
        )
        r.fulfill(content_type="text/html; charset=utf-8", body=html)

    page.context.route("https://www.facebook.com/**", route)
    worker = BrowserWorker(tmp_path)
    worker.context = page.context
    result = worker.execute("check_status", payload(url=""))
    assert result["outcome"] == "pending" and result["url"] == LINK


def test_checks_preserve_send_time_and_record_unknown_without_downgrade(store, job):
    store.update_job(job, source="browser", status="pending")
    sent = store.job(job)["sent_at"]
    store.record_check(job, "published", "Đúng bài", LINK)
    current = store.job(job)
    assert current["sent_at"] == sent and current["first_visible_at"] and current["checked_at"]
    store.record_check(job, "unknown", "Mạng lỗi")
    current = store.job(job)
    assert current["status"] == "published" and current["check_outcome"] == "unknown"
    assert current["url"] == LINK
    assert store.events(job)[0]["note"] == "Mạng lỗi"
    assert len(store.events(job)) == 3


def test_failed_check_is_atomic_and_does_not_invent_legacy_send_time(store, job):
    with pytest.raises(ValueError):
        store.record_check(job, "published", "Invalid without URL")
    assert store.job(job)["checked_at"] == "" and not store.events(job)
    store.record_check(job, "pending", "Đang chờ")
    assert store.job(job)["sent_at"] == ""


def test_reopen_recovers_interrupted_send_once_preserves_snapshot_and_history(store, job):
    store.update_job(job, status="sending")
    reopened = Store(store.root)
    try:
        # Creating a Store alone must not alter an active instance's sending state.
        assert reopened.job(job)["status"] == "sending"
        reopened.recover_interrupted()
        assert reopened.job(job)["status"] == "uncertain"
        assert reopened.recovered == [job]
        assert reopened.events(job)[0]["source"] == "recovery"
        assert reopened.job(job)["body"] == store.job(job)["body"]
        reopened.recover_interrupted()
        assert reopened.recovered == []
    finally:
        reopened.close()


def test_duplicate_detection_uses_content_and_image_bytes_not_post_title(store, task_data, app, tmp_path):
    posts, groups = task_data
    first = store.create_job(posts[0], groups[0])
    post = store.post(posts[0])
    copied_image = store.import_image(store.asset(post["images"][0]))
    cloned = store.save_post(None, "Tên mới", post["html"], post["plain"], post["tags"], [copied_image])
    assert [j["id"] for j in store.post_duplicates(cloned, [groups[0]])] == [first]
    assert not store.post_duplicates(cloned, [groups[1]])
    store.update_job(first, status="skipped")
    assert not store.post_duplicates(cloned, [groups[0]])


def test_tracking_queue_saves_results_continues_and_cannot_publish_at_same_time(
    window, store, task_data, monkeypatch
):
    batch = store.create_batch(task_data[0][0], task_data[1])
    jobs = store.batch_jobs(batch)
    for job in jobs:
        store.update_job(job["id"], status="pending")
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append((action, data)))
    window.start_checks([j["id"] for j in jobs])
    assert commands[0][0] == "check_status"
    with pytest.raises(ValueError):
        window.start_posting_queue()
    window.browser_done("check_status", {**commands[0][1], "outcome": "unknown", "message": "Không tìm thấy"})
    assert store.job(jobs[0]["id"])["check_outcome"] == "unknown"
    window.dispatch_check()
    assert commands[1][1]["job_id"] == jobs[1]["id"]
    window.stop_checks()
    window.browser_done("check_status", {**commands[1][1], "outcome": "pending", "message": "Chờ duyệt"})
    assert not window.monitor_running and len(commands) == 2
    monkeypatch.undo()


def test_periodic_check_respects_posting_and_rotates_oldest_unchecked(window, store, task_data, monkeypatch):
    batch = store.create_batch(task_data[0][0], task_data[1])
    jobs = store.batch_jobs(batch)
    for job in jobs:
        store.update_job(job["id"], status="submitted")
    store.record_check(jobs[0]["id"], "unknown", "Đã xem")
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append(data))
    window.queue_active = True
    window.periodic_check()
    assert commands == []
    window.queue_active = False
    window.periodic_check()
    assert commands[0]["job_id"] == jobs[1]["id"]
    window.stop_checks()
    window.finish_browser()
    monkeypatch.undo()


def test_manager_filters_actual_send_date_group_tag_and_exports_filtered(window, store, task_data, tmp_path):
    jobs = [store.create_job(task_data[0][0], g) for g in task_data[1]]
    store.update_job(jobs[0], status="submitted")
    with store.db:
        store.db.execute("UPDATE jobs SET sent_at=? WHERE id=?", (SENT_AT, jobs[0]))
    view = window.post_manager
    view.refresh()
    view.date_field.setCurrentIndex(view.date_field.findData("sent_at"))
    view.start.setDate(QDate(2026, 11, 17))
    view.end.setDate(QDate(2026, 11, 17))
    view.use_dates.setChecked(True)
    assert [j["id"] for j in view.filtered_jobs] == [jobs[0]]
    view.group.setCurrentIndex(view.group.findData(store.job(jobs[1])["group_url"]))
    assert view.table.rowCount() == 0
    view.use_dates.setChecked(False)
    assert view.table.rowCount() == 1
    view.group.setCurrentIndex(0)
    view.set_all_checked(True)
    assert len(view.selected_ids()) == 3
    view.refresh()
    assert len(view.selected_ids()) == 3
    output = tmp_path / "filtered.xlsx"
    store.export_excel(output, view.filtered_jobs[:1])
    from openpyxl import load_workbook

    book = load_workbook(output)
    assert book.active.max_row == 2 and book.active["L1"].value == "Gửi lúc (UTC)"
    book.close()


def test_cross_task_duplicate_send_block_and_confirmed_repost(window, store, task_data, monkeypatch):
    first = store.create_job(task_data[0][0], task_data[1][0])
    store.update_job(first, status="submitted")
    second = store.create_job(task_data[0][0], task_data[1][0])
    window.refresh_jobs(second)
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append(action))
    with pytest.raises(ValueError, match="cùng nội dung"):
        window.run_browser("publish")
    assert commands == []
    third = store.create_job(task_data[0][0], task_data[1][0], allow_duplicate=True)
    window.refresh_jobs(third)
    window.run_browser("publish")
    assert commands == ["publish"]
    window.finish_browser()
    monkeypatch.undo()


@pytest.mark.parametrize("label", ["Not approved", "Not yet published", "Unpublished"])
def test_negative_approval_labels_never_become_publication(page, label):
    prepare(page, card(f'<span role="status">{label}</span>'))
    assert inspect_page(page, payload())["outcome"] == "unknown"


def test_tracking_error_preserves_status_and_stops_remaining_checks(window, store, task_data, monkeypatch):
    jobs = [store.create_job(task_data[0][0], g) for g in task_data[1]]
    for job_id in jobs:
        store.update_job(job_id, status="pending")
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append(data))
    window.start_checks(jobs)
    window.browser_failed("check_status", "Facebook yêu cầu đăng nhập", commands[0])
    assert not window.monitor_running and not window.busy
    assert store.job(jobs[0])["status"] == "pending"
    assert store.job(jobs[0])["check_outcome"] == "unknown"
    assert store.job(jobs[1])["checked_at"] == ""
    monkeypatch.undo()


def test_resume_selects_remaining_batch_and_keeps_sent_snapshot(window, store, task_data):
    batch = store.create_batch(task_data[0][0], task_data[1])
    jobs = store.batch_jobs(batch)
    store.update_job(jobs[0]["id"], status="submitted")
    window.resume_saved_queue()
    assert window.batch_filter.currentData() == batch and window.tabs.currentIndex() == 2
    assert window.next_queue_job(batch)["id"] == jobs[1]["id"]
    post = store.post(task_data[0][0])
    store.save_post(post["id"], "Sửa tiêu đề", "<p>Mới</p>", "Mới", "", post["images"])
    assert store.job(jobs[1]["id"])["body"] == jobs[1]["body"]
    assert window.store.preference("last_batch") in {"", str(batch)}


def test_same_sent_job_cannot_be_republished(window, store, task_data):
    job_id = store.create_job(task_data[0][0], task_data[1][0])
    store.update_job(job_id, status="submitted")
    window.refresh_jobs(job_id)
    with pytest.raises(ValueError, match="đã được xử lý"):
        window.run_browser("publish")


def test_approval_words_in_comment_are_not_a_status_label(page):
    prepare(page, card("<p>Tôi mong bài này đã được phê duyệt sớm</p>"), LINK)
    assert inspect_page(page, payload())["outcome"] == "unknown"


def test_editing_status_does_not_invent_send_time(store, job):
    store.update_job(job, status="pending")
    assert store.job(job)["sent_at"] == ""
    store.update_job(job, source="browser", status="submitted")
    sent = store.job(job)["sent_at"]
    assert sent
    store.update_job(job, status="rejected")
    assert store.job(job)["sent_at"] == sent


@pytest.mark.parametrize("badge,tab", [("Published", "Pending"), ("Chờ duyệt", "Published")])
def test_conflicting_card_and_selected_category_stays_unknown(page, badge, tab):
    prepare(
        page,
        f'<div role="tab" aria-selected="true">{tab}</div>' + card(f'<div role="status">{badge}</div>'),
        GROUP + "your_content/",
    )
    assert inspect_page(page, payload(), own_content=True)["outcome"] == "unknown"
