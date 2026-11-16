import pytest
from PySide6.QtWidgets import QMessageBox, QPushButton


def prepare(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    posts, groups = task_data
    return [store.create_job(posts[0], groups[0]), store.create_job(posts[1], groups[1])]


def select(window, job_id):
    window.refresh_jobs(job_id)
    assert window.current_job()["id"] == job_id


def test_create_six_tasks_using_ui(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    window.tabs.setCurrentIndex(2)
    create = next(widget for widget in window.findChildren(QPushButton) if widget.text() == "Tạo lượt đăng")
    posts, groups = task_data
    for post_id in posts:
        for group_id in groups:
            window.job_posts.setCurrentIndex(window.job_posts.findData(post_id))
            window.job_groups.setCurrentIndex(window.job_groups.findData(group_id))
            create.click()
            assert window.current_job()["post_id"] == post_id
            assert window.current_job()["group_id"] == group_id
    assert window.history.rowCount() == 6
    assert len(store.jobs()) == 6


@pytest.mark.parametrize(
    "answer, expected", [(QMessageBox.StandardButton.No, 1), (QMessageBox.StandardButton.Yes, 2)]
)
def test_duplicate_task_requires_user_choice(window, store, task_data, monkeypatch, answer, expected):
    window.refresh_posts()
    window.refresh_groups()
    window.create_job()
    prompts = []

    def question(*args):
        prompts.append(args[2])
        return answer

    monkeypatch.setattr(QMessageBox, "question", question)
    window.create_job()
    assert len(store.jobs()) == expected
    assert len(prompts) == 1 and "Vẫn tạo lượt mới" in prompts[0]


def test_task_creation_rejects_unsaved_selected_post(window, store, task_data):
    window.refresh_posts()
    window.refresh_groups()
    window.post_id = window.job_posts.currentData()
    window.dirty = True
    with pytest.raises(ValueError, match="chưa lưu"):
        window.create_job()
    assert store.jobs() == []


def test_task_creation_requires_post_and_group(window):
    with pytest.raises(ValueError, match="ít nhất"):
        window.create_job()


def test_switch_tasks_routes_link_note_and_clipboard_to_correct_task(window, store, task_data, app):
    first, second = prepare(window, store, task_data)
    select(window, first)
    window.link.setText("https://facebook.com/groups/hr-0/posts/101/")
    window.job_note.setText("Kế toán chờ duyệt")
    window.status_choice.setCurrentIndex(window.status_choice.findData("pending"))
    window.save_status()
    select(window, second)
    assert window.link.text() == "" and window.job_note.text() == ""
    window.copy_job()
    assert app.clipboard().text() == store.job(second)["body"]
    window.link.setText("https://facebook.com/groups/hr-1/posts/202/")
    window.save_link()
    select(window, first)
    assert window.link.text().endswith("/posts/101/")
    assert window.job_note.text() == "Kế toán chờ duyệt"
    window.copy_link()
    assert app.clipboard().text() == store.job(first)["url"]
    assert store.job(second)["note"] == ""


def test_delayed_browser_result_updates_origin_task_after_selection_changes(window, store, task_data):
    first, second = prepare(window, store, task_data)
    select(window, second)
    window.browser_done("fill", {"job_id": first, "message": "Đã điền mô phỏng"})
    assert store.job(first)["status"] == "prepared"
    assert store.job(second)["status"] == "draft"
    assert window.current_job()["id"] == second
    window.browser_done(
        "read_link",
        {
            "job_id": first,
            "message": "Đã lấy link mô phỏng",
            "url": "https://facebook.com/groups/hr-0/posts/101/",
        },
    )
    assert store.job(first)["url"].endswith("/posts/101/")
    assert store.job(second)["url"] == ""
    assert window.link.text() == ""


def test_filling_again_does_not_downgrade_pending_task(window, store, task_data):
    first, _ = prepare(window, store, task_data)
    store.update_job(first, status="pending")
    window.browser_done("fill", {"job_id": first, "message": "Đã điền mô phỏng"})
    assert store.job(first)["status"] == "pending"


def test_busy_browser_blocks_second_task_and_buttons_reenable_after_failure(
    window, store, task_data, monkeypatch
):
    first, second = prepare(window, store, task_data)
    commands = []
    with monkeypatch.context() as patch:
        patch.setattr(window.browser, "submit", lambda action, payload: commands.append((action, payload)))
        patch.setattr(QMessageBox, "warning", lambda *args: None)
        select(window, first)
        window.run_browser("open_group")
        assert window.busy and all(not widget.isEnabled() for widget in window.browser_buttons)
        select(window, second)
        with pytest.raises(ValueError, match="Chờ thao tác"):
            window.run_browser("open_group")
        assert len(commands) == 1 and commands[0][1]["job_id"] == first
        window.browser_failed("open_group", "Lỗi mạng mô phỏng", commands[0][1])
        assert not window.busy and all(widget.isEnabled() for widget in window.browser_buttons)
        window.run_browser("open_group")
        assert commands[1][1]["job_id"] == second
        window.finish_browser()


def test_hidden_history_row_cannot_be_used_for_posting(window, store, task_data):
    first, _ = prepare(window, store, task_data)
    select(window, first)
    window.history_search.setText("Không có task phù hợp")
    assert window.history.isRowHidden(window.history.currentRow())
    with pytest.raises(ValueError, match="Chọn"):
        window.current_job()


def test_stale_screenshot_does_not_attach_to_changed_permalink(window, store, task_data, monkeypatch):
    first, _ = prepare(window, store, task_data)
    old_url = "https://www.facebook.com/groups/hr-0/posts/101/"
    store.update_job(first, url=old_url)
    image = store.root / "evidence" / "delayed.png"
    image.write_bytes(b"screenshot of 101")
    store.update_job(first, url="https://facebook.com/groups/hr-0/posts/202/")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    window.browser_done(
        "screenshot",
        {"job_id": first, "url": old_url, "evidence": "evidence/delayed.png", "message": "Đã chụp"},
    )
    assert store.job(first)["evidence"] == ""
    assert store.job(first)["url"].endswith("/posts/202/")
    assert warnings


@pytest.mark.parametrize("answer", [QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes])
def test_new_permalink_on_published_task_requires_confirmation(window, store, task_data, monkeypatch, answer):
    first, _ = prepare(window, store, task_data)
    old_url = "https://www.facebook.com/groups/hr-0/posts/101/"
    store.update_job(first, url=old_url, status="published")
    select(window, first)
    window.link.setText("https://facebook.com/groups/hr-0/posts/202/")
    prompts = []

    def question(*args):
        prompts.append(args[2])
        return answer

    monkeypatch.setattr(QMessageBox, "question", question)
    window.save_status()
    assert len(prompts) == 1
    saved = store.job(first)
    assert saved["url"] == (
        old_url
        if answer == QMessageBox.StandardButton.No
        else "https://www.facebook.com/groups/hr-0/posts/202/"
    )
    assert saved["status"] == "published"


def test_screenshot_result_updates_only_origin_task(window, store, task_data):
    first, second = prepare(window, store, task_data)
    url = "https://www.facebook.com/groups/hr-0/posts/101/"
    store.update_job(first, url=url)
    image = store.root / "evidence" / "origin.png"
    image.write_bytes(b"simulated screenshot")
    select(window, second)
    window.browser_done(
        "screenshot",
        {"job_id": first, "url": url, "evidence": "evidence/origin.png", "message": "Đã chụp mô phỏng"},
    )
    assert store.job(first)["evidence"] == "evidence/origin.png"
    assert store.job(first)["status"] == "draft"
    assert store.job(second)["evidence"] == ""
    assert window.current_job()["id"] == second
