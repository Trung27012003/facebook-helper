import sqlite3
import zipfile

import pytest
from openpyxl import load_workbook
from PySide6.QtGui import QColor, QImage

from facebook_helper.domain import normalize_group, post_url


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/groups/hr/",
        "https://facebook.com.evil.test/groups/hr/",
        "http://facebook.com/groups/hr/",
        "https://facebook.com@evil.test/groups/hr/",
        "https://facebook.com/groups/",
        "https://facebook.com/groups/feed/",
        "https://facebook.com:444/groups/hr/",
        "https://user@facebook.com/groups/hr/",
    ],
)
def test_reject_invalid_group(url):
    with pytest.raises(ValueError):
        normalize_group(url)


def test_normalize_and_permalink():
    assert (
        normalize_group("https://m.facebook.com/groups/hr/?ref=share")
        == "https://www.facebook.com/groups/hr/"
    )
    assert post_url(
        "https://facebook.com/groups/hr/permalink/123/?ref=share", "https://facebook.com/groups/hr/"
    ) == ("https://www.facebook.com/groups/hr/posts/123/")
    assert post_url(
        "https://facebook.com/groups/hr/?multi_permalinks=123", "https://facebook.com/groups/hr/"
    ).endswith("/posts/123/")


@pytest.mark.parametrize(
    "url",
    [
        "https://facebook.com/groups/hr/",
        "https://facebook.com/groups/other/posts/123/",
        "https://facebook.com/groups/hr/?multi_permalinks=1,2",
        "https://evil.test/groups/hr/posts/123/",
    ],
)
def test_reject_non_permalink(url):
    with pytest.raises(ValueError):
        post_url(url, "https://facebook.com/groups/hr/")


def test_snapshot_survives_changes_and_deletion(store, job):
    original = store.job(job)
    store.save_post(original["post_id"], "New", "<p>New</p>", "New", "", [])
    store.delete_post(original["post_id"])
    store.delete_group(original["group_id"])
    saved = store.job(job)
    assert saved["title"] == "Kế toán"
    assert saved["body"] == "Ứng tuyển\n\n#hr"
    assert saved["post_id"] is None and saved["group_id"] is None


def test_status_requires_actual_permalink(store, job):
    with pytest.raises(ValueError):
        store.update_job(job, status="published")
    with pytest.raises(ValueError):
        store.update_job(job, status="invented")
    store.update_job(job, status="pending")
    assert store.job(job)["status"] == "pending"
    store.update_job(job, status="published", url="https://facebook.com/groups/hr-hanoi/posts/123/")
    assert store.job(job)["status"] == "published"
    with pytest.raises(ValueError):
        store.update_job(job, url="")


def test_unique_groups_and_required_fields(store):
    with pytest.raises(ValueError):
        store.save_post(None, "", "", "", "", [])
    store.save_group(None, "One", "https://facebook.com/groups/hr/", "", "")
    with pytest.raises(ValueError):
        store.save_group(None, "Two", "https://m.facebook.com/groups/hr/", "", "")


def test_images_are_owned_and_preserved(app, store, tmp_path, job):
    original = tmp_path / "source.png"
    image = QImage(20, 20, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    assert image.save(str(original))
    relative = store.import_image(original)
    original.unlink()
    assert store.asset(relative).is_file()
    with pytest.raises(ValueError):
        store.asset("../../outside")
    with pytest.raises(ValueError):
        store.update_job(job, evidence="../../outside")


def test_export_neutralizes_formula_and_keeps_unicode(store, job, tmp_path):
    store.update_job(job, note='  =HYPERLINK("https://example.com")')
    output = tmp_path / "report.xlsx"
    store.export_excel(output)
    book = load_workbook(output)
    sheet = book.active
    assert sheet["B2"].value == "Kế toán"
    assert sheet["H2"].data_type == "s"
    assert sheet["H2"].value.startswith("'")
    assert sheet["K2"].value == "Ứng tuyển\n\n#hr"
    book.close()


def test_backup_consistent_and_excludes_session(store, job, tmp_path):
    (store.root / "browser" / "cookies").write_text("private")
    (store.root / "images" / "test.png").write_bytes(b"example")
    target = tmp_path / "backup.zip"
    store.backup(target)
    with zipfile.ZipFile(target) as archive:
        assert "images/test.png" in archive.namelist()
        assert not any(name.startswith("browser/") for name in archive.namelist())
        archive.extractall(tmp_path / "restore")
    with sqlite3.connect(tmp_path / "restore" / "helper.db") as db:
        assert db.execute("SELECT body FROM jobs WHERE id=?", (job,)).fetchone()[0] == "Ứng tuyển\n\n#hr"
    with pytest.raises(ValueError):
        store.backup(store.root / "backup.zip")
