import sqlite3

import pytest

from facebook_helper.domain import parse_tags
from facebook_helper.storage import Store
from facebook_helper.templates import recruitment_article


def test_tag_normalization_and_exact_matching(store):
    assert parse_tags(" #Hà Nội, hà nội; Kỹ thuật\nTUYỂN GẤP") == ["Hà Nội", "Kỹ thuật", "TUYỂN GẤP"]
    first = store.save_group(None, "A", "https://facebook.com/groups/a/", "Hà Nội, Kỹ thuật", "")
    second = store.save_group(None, "B", "https://facebook.com/groups/b/", "hà nội, Kế toán", "")
    store.save_group(None, "C", "https://facebook.com/groups/c/", "Hà Nội mở rộng", "")
    assert [group["id"] for group in store.groups_by_tag("#HÀ NỘI")] == [first, second]
    assert store.groups_by_tag("") == []
    assert store.groups_by_tag("Hà Nội, Kế toán") == []
    assert store.group_tags() == ["Hà Nội", "Hà Nội mở rộng", "Kế toán", "Kỹ thuật"]


def test_batch_deduplicates_groups_and_keeps_explicit_order(store, task_data):
    posts, groups = task_data
    batch = store.create_batch(posts[0], [groups[2], groups[0], groups[2]], "Đợt kỹ sư", "Hà Nội")
    jobs = store.batch_jobs(batch)
    assert [job["group_id"] for job in jobs] == [groups[2], groups[0]]
    assert [job["position"] for job in jobs] == [0, 1]
    assert store.batches()[0]["title"] == "Đợt kỹ sư"
    assert store.batches()[0]["total"] == 2
    assert store.batches()[0]["audience"] == "Hà Nội"


@pytest.mark.parametrize("group_ids", [[], [99999]])
def test_invalid_batch_does_not_create_partial_data(store, task_data, group_ids):
    with pytest.raises(ValueError):
        store.create_batch(task_data[0][0], group_ids)
    assert store.batches() == [] and store.jobs() == []


def test_batch_rolls_back_if_second_job_insert_fails(store, task_data, monkeypatch):
    original = store._insert_job
    calls = []

    def insert(*args):
        calls.append(args)
        if len(calls) == 2:
            raise sqlite3.OperationalError("simulated disk failure")
        return original(*args)

    monkeypatch.setattr(store, "_insert_job", insert)
    with pytest.raises(sqlite3.OperationalError):
        store.create_batch(task_data[0][0], task_data[1])
    assert store.batches() == [] and store.jobs() == []


def test_migrating_existing_v1_database_preserves_history(tmp_path):
    root = tmp_path / "v1"
    root.mkdir()
    with sqlite3.connect(root / "helper.db") as db:
        db.executescript("""
        CREATE TABLE posts(id INTEGER PRIMARY KEY,title TEXT NOT NULL,html TEXT NOT NULL,
            plain TEXT NOT NULL,tags TEXT NOT NULL DEFAULT '',images TEXT NOT NULL DEFAULT '[]',updated_at TEXT NOT NULL);
        CREATE TABLE groups(id INTEGER PRIMARY KEY,name TEXT NOT NULL,url TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '');
        CREATE TABLE jobs(id INTEGER PRIMARY KEY,post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
            group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,title TEXT NOT NULL,group_name TEXT NOT NULL,
            group_url TEXT NOT NULL,body TEXT NOT NULL,images TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',
            url TEXT NOT NULL DEFAULT '',evidence TEXT NOT NULL DEFAULT '',note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        INSERT INTO posts VALUES(1,'Bài cũ','<p>Nội dung</p>','Nội dung','','[]','2026-11-16T00:00:00+00:00');
        INSERT INTO groups VALUES(1,'Nhóm cũ','https://www.facebook.com/groups/old/','Hà Nội','');
        INSERT INTO jobs VALUES(1,1,1,'Bài cũ','Nhóm cũ','https://www.facebook.com/groups/old/',
            'Nội dung','[]','pending','','','Ghi chú cũ','2026-11-16T00:00:00+00:00','2026-11-16T00:00:00+00:00');
        PRAGMA user_version=1;
        """)
    for _ in range(2):
        upgraded = Store(root)
        try:
            assert upgraded.job(1)["body"] == "Nội dung"
            assert upgraded.job(1)["note"] == "Ghi chú cũ"
            assert upgraded.job(1)["status"] == "pending"
            assert upgraded.job(1)["batch_id"] is None
            assert upgraded.db.execute("PRAGMA user_version").fetchone()[0] == 5
        finally:
            upgraded.close()


def test_recruitment_template_matches_reference_layout_and_escapes_input(app):
    from PySide6.QtGui import QTextDocument

    article = recruitment_article(
        {
            "position": "Kỹ sư <PLC>",
            "company": "Công ty A & B",
            "region": "Hà Nội",
            "salary": "15–25 triệu/tháng",
            "duties": "Lập trình PLC\nThiết kế điện",
            "requirements": "Chào đón Fresher",
            "benefits": "Bảo hiểm",
            "location": "Hà Nội",
            "schedule": "Thứ 2–6",
            "email": "hr@example.com",
            "phone": "0123456789",
            "tags": "#TuyenDung",
        }
    )
    doc = QTextDocument()
    doc.setHtml(article["html"])
    text = doc.toPlainText()
    for expected in [
        "[HÀ NỘI] CÔNG TY A & B TUYỂN DỤNG KỸ SƯ <PLC>",
        "CƠ HỘI DÀNH CHO BẠN",
        "• Lập trình PLC",
        "YÊU CẦU",
        "QUYỀN LỢI",
        "15–25 triệu/tháng",
        "ỨNG TUYỂN NGAY",
        "hr@example.com",
    ]:
        assert expected in text
    assert "&lt;PLC&gt;" in article["html"]
    assert article["tags"] == "#TuyenDung"


def test_recruitment_template_requires_position_and_company():
    with pytest.raises(ValueError):
        recruitment_article({"position": "Kỹ sư"})


def test_job_snapshots_html_not_only_plain_text(store):
    post = store.save_post(None, "HTML", "<p><b>Đậm</b></p><ul><li>PLC</li></ul>", "Đậm\n• PLC", "#HR", [])
    group = store.save_group(None, "Nhóm", "https://facebook.com/groups/hr/", "", "")
    job = store.create_job(post, group)
    assert "<b>Đậm</b>" in store.job(job)["body_html"]
    assert "<ul>" in store.job(job)["body_html"] and "#HR" in store.job(job)["body_html"]
    store.save_post(post, "Đã sửa", "<p>Nội dung khác</p>", "Nội dung khác", "", [])
    assert "<b>Đậm</b>" in store.job(job)["body_html"]
