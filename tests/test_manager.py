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
        "Xuất Excel",
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
