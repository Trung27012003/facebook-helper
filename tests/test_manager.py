from PySide6.QtCore import QDate


def test_manager_filters_keyword_status_and_inclusive_dates(window, store, task_data):
    posts, groups = task_data
    first = store.create_job(posts[0], groups[0])
    second = store.create_job(posts[1], groups[1])
    with store.db:
        store.db.execute("UPDATE jobs SET created_at=? WHERE id=?", ("2026-11-01T12:00:00+00:00", first))
        store.db.execute("UPDATE jobs SET created_at=? WHERE id=?", ("2026-11-10T12:00:00+00:00", second))
    store.update_job(first, status="pending")
    view = window.post_manager
    view.refresh()
    assert view.table.rowCount() == 2
    view.keyword.setText("Kế toán")
    assert view.table.rowCount() == 1
    view.keyword.clear()
    view.use_dates.setChecked(True)
    view.start.setDate(QDate(2026, 11, 1))
    view.end.setDate(QDate(2026, 11, 1))
    assert view.table.rowCount() == 1
    view.status.setCurrentIndex(view.status.findData("pending"))
    assert view.table.rowCount() == 1
    view.status.setCurrentIndex(view.status.findData("published"))
    assert view.table.rowCount() == 0
    view.start.setDate(QDate(2026, 11, 15))
    assert "Ngày bắt đầu" in view.summary.text()
