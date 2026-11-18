import json
import zipfile

import pytest
from openpyxl import load_workbook

from facebook_helper.storage import Store


def create_matrix(store, task_data):
    posts, groups = task_data
    return {(post, group): store.create_job(post, group) for post in posts for group in groups}


def test_one_post_three_groups_have_independent_status_links_and_evidence(store, task_data):
    posts, groups = task_data
    ids = [store.create_job(posts[0], group) for group in groups]
    evidence = store.root / "evidence" / "first.png"
    evidence.write_bytes(b"test evidence")
    store.update_job(
        ids[0],
        status="published",
        url="https://facebook.com/groups/hr-0/posts/101/",
        evidence="evidence/first.png",
        note="Đã kiểm tra",
    )
    store.update_job(ids[1], status="pending", note="Chờ quản trị viên")
    jobs = [store.job(job_id) for job_id in ids]
    assert len(set(ids)) == 3
    assert [job["status"] for job in jobs] == ["published", "pending", "draft"]
    assert [job["url"] for job in jobs] == ["https://www.facebook.com/groups/hr-0/posts/101/", "", ""]
    assert [job["evidence"] for job in jobs] == ["evidence/first.png", "", ""]
    assert len({job["body"] for job in jobs}) == 1
    assert len({job["group_url"] for job in jobs}) == 3


def test_two_posts_three_groups_keep_correct_content_tags_and_images(store, task_data):
    matrix = create_matrix(store, task_data)
    assert len(matrix) == 6
    for (post_id, group_id), job_id in matrix.items():
        post, job = store.post(post_id), store.job(job_id)
        assert job["post_id"] == post_id and job["group_id"] == group_id
        assert job["title"] == post["title"]
        assert job["body"] == post["plain"] + "\n\n" + post["tags"]
        assert json.loads(job["images"]) == post["images"]
    assert store.post(task_data[0][0])["images"] != store.post(task_data[0][1])["images"]


def test_editing_post_and_group_only_affects_future_tasks(store, task_data):
    posts, groups = task_data
    job_id = store.create_job(posts[0], groups[0])
    before = store.job(job_id)
    new_images = store.post(posts[1])["images"]
    store.save_post(posts[0], "Tên mới", "<p>Nội dung mới</p>", "Nội dung mới", "#new", new_images)
    store.save_group(
        groups[0],
        "Tên nhóm mới",
        "https://facebook.com/groups/hr-new/",
        "",
        "",
        position_ids=[store.positions()[0]["id"]],
    )
    assert store.job(job_id) == before
    new_job = store.job(store.create_job(posts[0], groups[0]))
    assert new_job["body"] == "Nội dung mới\n\n#new"
    assert new_job["group_url"].endswith("/hr-new/")
    assert json.loads(new_job["images"]) == new_images


def test_all_tasks_persist_when_database_is_reopened(store, task_data):
    matrix = create_matrix(store, task_data)
    job_id = next(iter(matrix.values()))
    store.update_job(job_id, status="pending", note="Kiểm tra sau khi mở lại")
    reopened = Store(store.root)
    try:
        assert reopened.jobs() == store.jobs()
        assert len(reopened.jobs()) == 6
    finally:
        reopened.close()


def test_invalid_update_is_atomic_and_does_not_touch_other_tasks(store, task_data):
    matrix = create_matrix(store, task_data)
    before = store.jobs()
    with pytest.raises(ValueError):
        store.update_job(
            next(iter(matrix.values())),
            status="published",
            url="https://facebook.com/groups/wrong/posts/101/",
            note="Không được lưu",
        )
    assert store.jobs() == before


@pytest.mark.parametrize("missing", ["post", "group"])
def test_missing_input_creates_no_partial_task(store, task_data, missing):
    posts, groups = task_data
    with pytest.raises(ValueError):
        store.create_job(99999 if missing == "post" else posts[0], 99999 if missing == "group" else groups[0])
    assert store.jobs() == []


def test_excel_exports_each_post_group_pair_once(store, task_data, tmp_path):
    matrix = create_matrix(store, task_data)
    store.update_job(next(iter(matrix.values())), status="pending", note="Một lượt chờ duyệt")
    path = tmp_path / "matrix.xlsx"
    store.export_excel(path)
    book = load_workbook(path)
    try:
        rows = list(book.active.iter_rows(min_row=2, values_only=True))
        assert len(rows) == 6
        assert len({row[0] for row in rows}) == 6
        assert {(row[1], row[2]) for row in rows} == {
            (store.post(post_id)["title"], store.job(job_id)["group_name"])
            for (post_id, _), job_id in matrix.items()
        }
        assert sum(row[4] == "Chờ duyệt" for row in rows) == 1
        for row in rows:
            assert row[10] == store.job(row[0])["body"]
    finally:
        book.close()


def test_backup_restore_keeps_all_tasks_and_uploaded_images(store, task_data, tmp_path):
    create_matrix(store, task_data)
    target = tmp_path / "matrix.zip"
    store.backup(target)
    restored_root = tmp_path / "restored"
    with zipfile.ZipFile(target) as archive:
        archive.extractall(restored_root)
    restored = Store(restored_root)
    try:
        assert restored.jobs() == store.jobs()
        for job in restored.jobs():
            for image in json.loads(job["images"]):
                assert restored.asset(image).read_bytes() == store.asset(image).read_bytes()
    finally:
        restored.close()


def test_changing_post_link_invalidates_old_evidence_and_confirmation(store, job):
    path = store.root / "evidence" / "old.png"
    path.write_bytes(b"old image")
    store.update_job(job, url="https://facebook.com/groups/hr-hanoi/posts/101/", status="published")
    store.update_job(job, evidence="evidence/old.png")
    store.update_job(job, url="https://facebook.com/groups/hr-hanoi/posts/202/")
    saved = store.job(job)
    assert saved["evidence"] == "", "Old screenshot must not describe a different post"
    assert saved["status"] != "published", "New permalink needs confirmation again"
    assert path.is_file(), "Historical files must not be deleted"


def test_equivalent_permalink_keeps_existing_evidence(store, job):
    path = store.root / "evidence" / "same.png"
    path.write_bytes(b"same image")
    store.update_job(job, url="https://facebook.com/groups/hr-hanoi/posts/101/", status="published")
    store.update_job(job, evidence="evidence/same.png")
    store.update_job(job, url="https://m.facebook.com/groups/hr-hanoi/permalink/101/?ref=share")
    assert store.job(job)["status"] == "published"
    assert store.job(job)["evidence"] == "evidence/same.png"
