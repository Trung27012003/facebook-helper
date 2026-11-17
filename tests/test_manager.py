from PySide6.QtCore import QDate
from PySide6.QtWidgets import QPushButton


def test_explicit_keyword_search_and_refresh_preserve_applied_filters(window, store, task_data):
    posts, groups = task_data
    ids = [store.create_job(p, groups[0]) for p in posts]
    view = window.post_manager
    view.refresh()
    assert view.table.rowCount() == 2
    view.keyword.setText("Kế toán")
    view.refresh()
    assert view.table.rowCount() == 2
    view.search_button.click()
    assert [j["id"] for j in view.filtered_jobs] == [ids[0]]
    view.keyword.setText("Kinh doanh")
    view.refresh()
    assert [j["id"] for j in view.filtered_jobs] == [ids[0]]
    view.keyword.returnPressed.emit()
    assert [j["id"] for j in view.filtered_jobs] == [ids[1]]


def test_batch_filter_distinguishes_repeated_campaigns(window, store, task_data):
    first = store.create_batch(task_data[0][0], task_data[1], title="Đợt sáng")
    second = store.create_batch(task_data[0][0], task_data[1], title="Đợt chiều", allow_duplicate=True)
    view = window.post_manager
    view.refresh()
    view.batch.setCurrentIndex(view.batch.findData(first))
    assert len(view.filtered_jobs) == 6
    view.search()
    assert {j["batch_id"] for j in view.filtered_jobs} == {first}
    assert len(view.filtered_jobs) == 3
    view.batch.setCurrentIndex(view.batch.findData(second))
    view.search()
    assert {j["batch_id"] for j in view.filtered_jobs} == {second}
    view.batch.setCurrentIndex(0)
    view.keyword.setText("Đợt sáng")
    view.search()
    assert {j["batch_id"] for j in view.filtered_jobs} == {first}


def test_invalid_date_range_preserves_previous_results(window, store, job):
    view = window.post_manager
    view.refresh()
    before = view.filtered_jobs[:]
    view.start.setDate(QDate(2026, 11, 20))
    view.end.setDate(QDate(2026, 11, 1))
    view.search()
    assert "Từ ngày" in view.summary.text() and view.filtered_jobs == before


def test_minimal_manager_actions(window):
    view = window.post_manager
    assert {b.text() for b in view.findChildren(QPushButton)} == {
        "Tìm kiếm",
        "Mở bài",
        "Sao chép link",
        "Mở nhóm",
        "Xuất Excel",
        "Xóa",
    }
    assert not hasattr(view, "details_panel") and not hasattr(view, "monitor_message")


def test_register_uses_attempt_time_without_inventing_sent_at(store, job):
    store.update_job(job, status="sending")
    attempt = store.events(job)[0]["happened_at"]
    store.update_job(job, status="uncertain")
    with store.db:
        store.db.execute("UPDATE jobs SET created_at='2020-01-01T00:00:00+00:00' WHERE id=?", (job,))
    record = store.posting_register()[0]
    assert record["activity_at"] == attempt and not record["sent_at"]


def test_delete_selected_record_keeps_facebook_link_and_duplicate_receipt(
    window, store, task_data, monkeypatch
):
    from PySide6.QtWidgets import QMessageBox

    post, group = task_data[0][0], task_data[1][0]
    job_id = store.create_job(post, group)
    link = store.job(job_id)["group_url"] + "posts/777/"
    store.update_job(job_id, source="browser", status="pending", url=link)
    view = window.post_manager
    view.refresh()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(
        window.browser,
        "submit",
        lambda *args: __import__("pytest").fail("Local deletion must not touch Facebook"),
    )
    view.delete_records()
    assert view.table.rowCount() == 0
    assert store.job(job_id)["url"] == link and store.job(job_id)["status"] == "pending"
    assert store.job(job_id)["hidden_at"]
    assert [j["id"] for j in store.post_duplicates(post, [group])] == [job_id]
    assert window.next_queue_job(store.job(job_id)["batch_id"]) is None


def test_cancel_delete_does_not_change_records(window, store, job, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    store.update_job(job, status="submitted")
    view = window.post_manager
    view.refresh()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    view.delete_records()
    assert view.table.rowCount() == 1 and not store.job(job)["hidden_at"]


def test_bulk_delete_only_sent_records_in_applied_search(window, store, task_data, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    posts, groups = task_data
    first = store.create_batch(posts[0], groups)
    other = store.create_batch(posts[1], groups)
    jobs = store.batch_jobs(first)
    for job in jobs[:2]:
        store.update_job(job["id"], status="submitted")
    for job in store.batch_jobs(other):
        store.update_job(job["id"], status="pending")
    view = window.post_manager
    view.refresh()
    view.batch.setCurrentIndex(view.batch.findData(first))
    view.search()
    view.batch.setCurrentIndex(
        view.batch.findData(other)
    )  # Draft controls do not change the applied results.
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    view.delete_records(True)
    assert [j["id"] for j in view.filtered_jobs] == [jobs[2]["id"]]
    assert not any(j["hidden_at"] for j in store.batch_jobs(other))
    assert all(store.job(j["id"])["hidden_at"] for j in jobs[:2])
    assert not store.job(jobs[2]["id"])["hidden_at"]


def test_delete_storage_is_atomic_and_survives_reopen(store, task_data):
    import pytest

    from facebook_helper.storage import Store

    sent = store.create_job(task_data[0][0], task_data[1][0])
    running = store.create_job(task_data[0][1], task_data[1][1])
    store.update_job(sent, status="pending")
    store.update_job(running, status="sending")
    with pytest.raises(ValueError):
        store.remove_posted_records([sent, running])
    assert not store.job(sent)["hidden_at"]
    store.remove_posted_records([sent])
    reopened = Store(store.root)
    try:
        assert sent not in [j["id"] for j in reopened.posting_register()]
        assert reopened.job(sent)["status"] == "pending"
    finally:
        reopened.close()


def test_manager_starts_today_and_excludes_yesterdays_posts(window, store, task_data):
    from datetime import datetime, timedelta

    jobs = [store.create_job(task_data[0][0], g) for g in task_data[1][:2]]
    yesterday = (datetime.now().astimezone() - timedelta(days=1)).isoformat()
    with store.db:
        store.db.execute("UPDATE jobs SET created_at=? WHERE id=?", (yesterday, jobs[0]))
    view = window.post_manager
    view.refresh()
    assert view.start.date() == view.end.date() == QDate.currentDate()
    assert [j["id"] for j in view.filtered_jobs] == [jobs[1]]
    view.start.setDate(QDate.currentDate().addDays(-1))
    view.search()
    view.refresh()
    assert len(view.filtered_jobs) == 2 and view.start.date() == QDate.currentDate().addDays(-1)


def test_default_today_rolls_over_but_manual_filter_does_not(window, monkeypatch):
    import facebook_helper.manager as module

    today = QDate.currentDate()

    class ClockDate(QDate):
        @staticmethod
        def currentDate():
            return today.addDays(1)

    view = window.post_manager
    monkeypatch.setattr(module, "QDate", ClockDate)
    view.refresh()
    assert view.start.date() == view.end.date() == today.addDays(1)
    view.start.setDate(today.addDays(-10))
    view.end.setDate(today)
    view.search()
    view.refresh()
    assert view.start.date() == today.addDays(-10) and view.end.date() == today


def test_open_group_uses_selected_record_even_without_post_link(window, store, task_data, monkeypatch):
    from PySide6.QtGui import QDesktopServices

    ids = [store.create_job(task_data[0][0], g) for g in task_data[1][:2]]
    view = window.post_manager
    view.refresh()
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))
    view.table.setCurrentCell(1, 0)
    selected = view.current_job_record()
    assert view.group_button.isEnabled() and not view.open_button.isEnabled()
    view.group_button.click()
    assert opened == [selected["group_url"]]
    assert selected["id"] in ids
    view.keyword.setText("Không có kết quả")
    view.search()
    assert not view.group_button.isEnabled()
