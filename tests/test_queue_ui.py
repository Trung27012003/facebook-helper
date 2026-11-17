import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox


def batch_for_window(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    batch = store.create_batch(task_data[0][0], task_data[1], "Kỹ sư tháng 11")
    window.refresh_batches(batch)
    window.refresh_jobs()
    return batch, store.batch_jobs(batch)


def test_tag_selects_all_matching_groups_and_allows_exclusions(window, store, task_data):
    posts, groups = task_data
    for index, group_id in enumerate(groups):
        group = next(g for g in store.groups() if g["id"] == group_id)
        store.save_group(
            group_id, group["name"], group["url"], "Hà Nội, Kỹ thuật" if index < 2 else "Hồ Chí Minh", ""
        )
    window.refresh_posts()
    window.refresh_groups()
    window.audience_mode.setCurrentIndex(2)
    window.audience_tag.setCurrentText("Hà Nội")
    assert window.selected_group_ids() == groups[:2]
    window.audience_list.item(1).setCheckState(Qt.CheckState.Unchecked)
    batch = window.create_posting_batch()
    assert [job["group_id"] for job in store.batch_jobs(batch)] == groups[:1]
    assert store.batches()[0]["audience"] == "Hà Nội"


def test_manual_multiselect_creates_one_ordered_batch(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    window.audience_mode.setCurrentIndex(1)
    window.audience_list.item(0).setCheckState(Qt.CheckState.Checked)
    window.audience_list.item(2).setCheckState(Qt.CheckState.Checked)
    batch = window.create_posting_batch()
    assert [job["group_id"] for job in store.batch_jobs(batch)] == [task_data[1][0], task_data[1][2]]
    assert window.batch_filter.currentData() == batch


def test_guided_queue_prepares_in_order_and_resume_skips_finished_groups(
    window, store, task_data, monkeypatch
):
    batch, jobs = batch_for_window(window, store, task_data)
    window.auto_send.setChecked(False)
    sent = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: sent.append((action, payload)))
        window.start_posting_queue()
        assert sent[0][0] == "prepare" and sent[0][1]["job_id"] == jobs[0]["id"]
        window.browser_done("prepare", {**sent[0][1], "filled": True, "message": "Đã chuẩn bị"})
        assert store.job(jobs[0]["id"])["status"] == "prepared"
        patch.setattr(QInputDialog, "getItem", lambda *args: ("Đã gửi, đang chờ duyệt", True))
        window.complete_queue_job()
        assert store.job(jobs[0]["id"])["status"] == "pending"
        assert sent[1][1]["job_id"] == jobs[1]["id"]
        window.browser_done("prepare", {**sent[1][1], "filled": True, "message": "Đã chuẩn bị"})
        window.pause_posting_queue()
        window.start_posting_queue()
        assert sent[2][1]["job_id"] == jobs[1]["id"]
        window.finish_browser()
        window.pause_posting_queue()


def test_automatic_queue_runs_all_groups_without_confirmation_between_posts(
    window, store, task_data, monkeypatch
):
    _, jobs = batch_for_window(window, store, task_data)
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: commands.append((action, payload)))
        patch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
        window.start_posting_queue()
        for index, job in enumerate(jobs):
            assert commands[index][1]["job_id"] == job["id"]
            window.browser_done(
                "publish", {**commands[index][1], "filled": True, "sent": True, "message": "Đã gửi"}
            )
            assert window.queue_timer.isActive()
            window.queue_timer.stop()
            window.queue_continue()
        assert len(commands) == len(jobs)
        assert window.queue_progress_bar.value() == len(jobs)
        assert not window.queue_active
        assert all(store.job(j["id"])["status"] == "submitted" for j in jobs)


def test_uncertain_submission_stops_and_blocks_automatic_retry(window, store, task_data, monkeypatch):
    _, jobs = batch_for_window(window, store, task_data)
    window.auto_send.setChecked(True)
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: commands.append((action, payload)))
        patch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
        window.start_posting_queue()
        window.browser_done(
            "publish", {**commands[0][1], "filled": True, "uncertain": True, "message": "Chưa rõ kết quả"}
        )
        assert not window.queue_active and not window.queue_timer.isActive()
        assert store.job(jobs[0]["id"])["status"] == "uncertain"
        with pytest.raises(ValueError, match="tránh gửi trùng"):
            window.start_posting_queue()
        assert len(commands) == 1


def test_queue_resuming_after_interrupted_process_requires_verification(window, store, task_data):
    _, jobs = batch_for_window(window, store, task_data)
    store.update_job(jobs[0]["id"], status="sending")
    with pytest.raises(ValueError, match="kiểm tra"):
        window.start_posting_queue()
    assert store.job(jobs[0]["id"])["status"] == "uncertain"


def test_switching_batch_pauses_auto_timer_and_keeps_tasks_separate(window, store, task_data):
    first, jobs = batch_for_window(window, store, task_data)
    second = store.create_batch(task_data[0][1], [task_data[1][0]], "Kế toán")
    window.refresh_batches(first)
    window.refresh_jobs(jobs[0]["id"])
    window.queue_active = True
    window.queue_auto = True
    window.queue_timer.start(30000)
    window.batch_filter.setCurrentIndex(window.batch_filter.findData(second))
    assert not window.queue_active and not window.queue_timer.isActive()
    visible = [
        int(window.history.item(row, 0).text())
        for row in range(window.history.rowCount())
        if not window.history.isRowHidden(row)
    ]
    assert visible == [store.batch_jobs(second)[0]["id"]]


def test_submitted_post_is_skipped_when_resuming_queue(window, store, task_data):
    batch, jobs = batch_for_window(window, store, task_data)
    store.update_job(jobs[0]["id"], status="submitted")
    assert window.next_queue_job(batch)["id"] == jobs[1]["id"]


def test_skip_group_continues_only_current_batch(window, store, task_data, monkeypatch):
    batch, jobs = batch_for_window(window, store, task_data)
    other = store.create_batch(task_data[0][1], [task_data[1][0]])
    window.refresh_jobs(jobs[0]["id"])
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: commands.append((action, payload)))
        patch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
        window.skip_queue_job()
        assert store.job(jobs[0]["id"])["status"] == "skipped"
        assert commands[0][1]["job_id"] == jobs[1]["id"]
        assert store.batch_jobs(other)[0]["status"] == "draft"
        window.finish_browser()
        window.pause_posting_queue()


def test_creating_another_batch_requires_pausing_running_queue(window, store, task_data):
    batch, _ = batch_for_window(window, store, task_data)
    window.queue_active = True
    with pytest.raises(ValueError, match="Tạm dừng"):
        window.create_posting_batch()
    assert len(store.batches()) == 1 and window.batch_filter.currentData() == batch
    window.pause_posting_queue()


def test_batch_history_follows_posting_order(window, store, task_data):
    _, jobs = batch_for_window(window, store, task_data)
    visible = [
        int(window.history.item(index, 0).text())
        for index in range(window.history.rowCount())
        if not window.history.isRowHidden(index)
    ]
    assert visible == [job["id"] for job in jobs]


@pytest.mark.parametrize("started, status", [(False, "error"), (True, "uncertain")])
def test_publish_failure_stops_queue_with_correct_retry_state(
    window, store, task_data, monkeypatch, started, status
):
    _, jobs = batch_for_window(window, store, task_data)
    store.update_job(jobs[0]["id"], status="sending")
    window.queue_active = True
    window.queue_auto = True
    window.queue_timer.start(30000)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    window.browser_failed(
        "publish", "Lỗi thử nghiệm", {"job_id": jobs[0]["id"], "submission_started": started}
    )
    assert not window.queue_active and not window.queue_timer.isActive()
    assert store.job(jobs[0]["id"])["status"] == status
    assert store.job(jobs[1]["id"])["status"] == "draft"


def test_pause_during_publish_does_not_advance_when_result_arrives(window, store, task_data):
    _, jobs = batch_for_window(window, store, task_data)
    store.update_job(jobs[0]["id"], status="sending")
    window.queue_active = True
    window.queue_auto = True
    window.pause_posting_queue()
    window.browser_done(
        "publish", {"job_id": jobs[0]["id"], "filled": True, "sent": True, "message": "Đã gửi"}
    )
    assert store.job(jobs[0]["id"])["status"] == "submitted"
    assert store.job(jobs[1]["id"])["status"] == "draft"
    assert not window.queue_active and not window.queue_timer.isActive()


def test_auto_mode_is_default_and_button_explains_its_action(window):
    assert window.auto_send.isChecked()
    assert window.begin_posting_button.text() == "Bắt đầu đăng"
    assert window.mode_badge.text() == "Tự đăng"
    window.auto_send.setChecked(False)
    assert window.begin_posting_button.text() == "Chuẩn bị bài"


def test_publish_open_draft_requires_confirmation_and_uses_recovery_action(
    window, store, task_data, monkeypatch
):
    _, jobs = batch_for_window(window, store, task_data)
    window.refresh_jobs(jobs[0]["id"])
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: commands.append((action, payload)))
        patch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
        window.publish_open_draft()
        assert commands == []
        patch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
        window.publish_open_draft()
        assert commands[0][0] == "publish_current"
        assert store.job(jobs[0]["id"])["status"] == "sending"
        window.browser_done(
            "publish_current", {**commands[0][1], "filled": True, "sent": True, "message": "Đã bấm Đăng"}
        )
        assert store.job(jobs[0]["id"])["status"] == "submitted"
        assert not window.queue_active


def test_verified_publication_saves_status_and_url_atomically(window, store, task_data):
    _, jobs = batch_for_window(window, store, task_data)
    store.update_job(jobs[0]["id"], status="sending")
    window.browser_done(
        "publish",
        {
            "job_id": jobs[0]["id"],
            "filled": True,
            "sent": True,
            "status": "published",
            "url": "https://www.facebook.com/groups/hr-0/posts/999/",
            "message": "Đã thấy bài",
        },
    )
    saved = store.job(jobs[0]["id"])
    assert saved["status"] == "published" and saved["url"].endswith("/posts/999/")


@pytest.mark.parametrize("status,has_link", [("pending", True), ("pending", False), ("submitted", True)])
def test_link_saved_before_auto_next_without_approval(
    window, store, task_data, monkeypatch, status, has_link
):
    _, jobs = batch_for_window(window, store, task_data)
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append((action, data)))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.start_posting_queue()
    link = jobs[0]["group_url"] + "posts/777/"
    window.browser_done(
        "publish",
        {
            **commands[0][1],
            "filled": True,
            "sent": True,
            "status": status,
            "message": "Đã gửi",
            **({"url": link} if has_link else {}),
        },
    )
    first = store.job(jobs[0]["id"])
    assert first["status"] == status and first["sent_at"]
    assert first["url"] == (link if has_link else "")
    assert not first["checked_at"] and not first["first_visible_at"]
    assert window.queue_timer.isActive()
    window.queue_timer.stop()
    window.queue_continue()
    assert commands[1][1]["job_id"] == jobs[1]["id"]
    window.finish_browser()
    window.pause_posting_queue()


def test_verified_link_kept_even_when_send_confirmation_uncertain(window, store, task_data, monkeypatch):
    _, jobs = batch_for_window(window, store, task_data)
    commands = []
    monkeypatch.setattr(window.browser, "submit", lambda action, data: commands.append(data))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.start_posting_queue()
    link = jobs[0]["group_url"] + "posts/777/"
    window.browser_done(
        "publish",
        {
            **commands[0],
            "filled": True,
            "uncertain": True,
            "sent": False,
            "link_captured": True,
            "url": link,
            "message": "Cần xem lại",
        },
    )
    record = store.job(jobs[0]["id"])
    assert record["status"] == "uncertain" and record["url"] == link
    assert not record["sent_at"] and not window.queue_active and len(commands) == 1


def test_finished_batch_highlights_results_hides_start_and_stale_instructions(window, store, task_data):
    batch, jobs = batch_for_window(window, store, task_data)
    window.set_posting_step(3)
    for job in jobs:
        store.update_job(job["id"], source="browser", status="pending", url=job["group_url"] + "posts/777/")
    window.current_action.setText("Hãy mở ô tạo bài trên Facebook, rồi bấm Điền bài.")
    window.refresh_jobs(jobs[0]["id"])
    window.update_queue_progress()
    assert window.run_state.text() == "Hoàn tất"
    assert window.queue_progress.text() == "3/3 nhóm"
    assert window.begin_posting_button.isHidden() and not window.begin_posting_button.isEnabled()
    assert window.pause_posting_button.isHidden() and window.current_action.isHidden()
    assert window.results_button.property("primary")
    assert not window.history.isColumnHidden(5) and window.history.isColumnHidden(4)
    assert window.history.item(0, 3).text() == "Đã gửi"
    assert window.result_copy_button.isEnabled()
    window.post_manager.keyword.setText("Từ khóa của lần tìm trước")
    window.results_button.click()
    assert len(window.post_manager.filtered_jobs) == 3
    assert window.tabs.currentIndex() == 3 and window.post_manager.criteria[0] == batch


def test_posting_controls_follow_running_and_paused_state(window, store, task_data):
    _, jobs = batch_for_window(window, store, task_data)
    window.set_posting_step(3)
    window.update_queue_progress()
    assert window.begin_posting_button.isEnabled() and not window.begin_posting_button.isHidden()
    assert not window.begin_posting_button.text().startswith("Tiếp tục")
    store.update_job(jobs[0]["id"], status="submitted")
    window.queue_active = True
    window.busy = True
    window.update_queue_progress()
    assert window.begin_posting_button.isHidden() and not window.pause_posting_button.isHidden()
    assert not window.new_batch_button.isEnabled()
    window.busy = False
    window.pause_posting_queue()
    assert window.begin_posting_button.text() == "Tiếp tục đăng" and window.begin_posting_button.isEnabled()
    assert window.pause_posting_button.isHidden()


def test_open_group_from_posting_results_does_not_interrupt_worker(window, store, task_data, monkeypatch):
    from PySide6.QtGui import QDesktopServices

    _, jobs = batch_for_window(window, store, task_data)
    window.refresh_jobs(jobs[1]["id"])
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))
    monkeypatch.setattr(
        window.browser, "submit", lambda *args: pytest.fail("Do not navigate the posting worker")
    )
    assert window.result_group_button.isEnabled() and not window.result_copy_button.isEnabled()
    window.result_group_button.click()
    assert opened == [jobs[1]["group_url"]]
