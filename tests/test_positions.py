import unicodedata

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QInputDialog, QMessageBox

from facebook_helper.choices import CheckPicker
from facebook_helper.storage import Store


def save_group(store, name, positions, tags=""):
    return store.save_group(None, name, f"https://facebook.com/groups/{name}/", tags, "", positions)


def test_catalog_normalizes_names_and_rejects_duplicates(store):
    name = unicodedata.normalize("NFD", "  Kỹ   sư PLC  ")
    position = store.save_position(None, name, "  ghi chú  ")
    value = next(p for p in store.positions() if p["id"] == position)
    assert value["name"] == "Kỹ sư PLC" and value["notes"] == "ghi chú"
    with pytest.raises(ValueError, match="đã có"):
        store.save_position(None, "KỸ SƯ PLC")
    with pytest.raises(ValueError, match="Nhập tên"):
        store.save_position(None, " \n ")
    with pytest.raises(ValueError, match="không còn"):
        store.save_position(9999, "Không có")


@pytest.mark.parametrize("positions", [None, [], [9999], [True], ["1"]])
def test_group_requires_real_positions_and_never_partially_saves(store, positions):
    with pytest.raises(ValueError):
        save_group(store, "test", positions)
    assert store.groups() == []


def test_group_multiple_positions_replace_atomically_and_rename_tracks_id(store):
    first = store.positions()[0]["id"]
    second = store.save_position(None, "Kế toán")
    group = save_group(store, "test", [first, second, first], "Hà Nội, Tuyển gấp, hà nội")
    value = store.groups()[0]
    assert value["position_ids"] == [first, second]
    assert value["category"] == "Hà Nội, Tuyển gấp"
    with pytest.raises(ValueError):
        store.save_group(group, "changed", value["url"], "lost", "", [second, 9999])
    assert store.groups()[0] == value
    store.save_group(group, "test", value["url"], value["category"], "", [second])
    store.save_position(second, "Kế toán trưởng")
    assert store.groups()[0]["position_names"] == ["Kế toán trưởng"]
    assert next(p for p in store.positions() if p["id"] == first)["group_count"] == 0
    with pytest.raises(ValueError, match="đang dùng"):
        store.delete_position(second)
    store.delete_group(group)
    store.delete_position(second)
    assert not store.db.execute("SELECT * FROM group_positions").fetchall()


def test_union_filters_multiple_positions_and_tags_without_duplicates(store):
    a = store.positions()[0]["id"]
    b = store.save_position(None, "Kế toán")
    c = store.save_position(None, "Lái xe")
    g1 = save_group(store, "a", [a, b], "Hà Nội, Tuyển gấp")
    g2 = save_group(store, "b", [b], "Đà Nẵng")
    save_group(store, "c", [c], "Hà Nội mở rộng")
    assert [g["id"] for g in store.groups_for_selection([a, b, a])] == [g1, g2]
    assert [g["id"] for g in store.groups_for_selection(tags=["#hÀ nỘI", "ĐÀ NẴNG"])] == [g1, g2]
    assert store.groups_for_selection() == []
    with pytest.raises(ValueError):
        store.groups_for_selection([9999])


def test_migration_from_schema6_preserves_groups_jobs_tags_and_requires_classification(tmp_path):
    root = tmp_path / "old"
    original = Store(root)
    with original.db:
        original.db.execute("DROP TABLE group_positions")
        original.db.execute("DROP TABLE positions")
        original.db.execute("PRAGMA user_version=6")
        original.db.execute(
            "INSERT INTO groups(name,url,category,notes) VALUES('Nhóm cũ','https://www.facebook.com/groups/old/','HN, HR','cũ')"
        )
    post = original.save_post(None, "Bài", "<p>Nội dung</p>", "Nội dung", "#hr", [])
    job = original.create_job(post, 1)
    before = original.job(job)
    original.close()
    upgraded = Store(root)
    try:
        assert upgraded.db.execute("PRAGMA user_version").fetchone()[0] == 7
        group = upgraded.groups()[0]
        assert group["category"] == "HN, HR" and group["notes"] == "cũ"
        assert group["position_ids"] == [] and upgraded.positions() == []
        assert upgraded.job(job) == before
        assert upgraded.groups_for_selection(tags=["HN"])[0]["id"] == group["id"]
        with pytest.raises(ValueError, match="ít nhất"):
            upgraded.save_group(group["id"], group["name"], group["url"], group["category"], "")
        position = upgraded.save_position(None, "Kỹ sư")
        upgraded.save_group(group["id"], group["name"], group["url"], group["category"], "", [position])
        assert upgraded.job(job) == before
    finally:
        upgraded.close()


def test_checkbox_picker_toggles_whole_rows_once_and_search_preserves_selection(app):
    picker = CheckPicker()
    picker.set_items([(1, "Kỹ sư"), (2, "Kế toán")])
    picker.show()
    picker.click()
    app.processEvents()
    rect = picker.list.visualItemRect(picker.list.item(0))
    QTest.mouseClick(picker.list.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert picker.checked_data() == [1]
    QTest.mouseClick(
        picker.list.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(rect.left() + 10, rect.center().y())
    )
    assert picker.checked_data() == []
    picker.set_checked([1])
    picker.search.setText("toán")
    assert picker.list.item(0).isHidden() and picker.checked_data() == [1]
    rect = picker.list.visualItemRect(picker.list.item(1))
    QTest.mouseClick(picker.list.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert picker.checked_data() == [1, 2]
    picker.set_items([(1, "Kỹ sư PLC"), (2, "Kế toán"), (3, "HR")])
    assert picker.checked_data() == [1, 2] and picker.labels()[0] == "Kỹ sư PLC"
    picker.popup.close()
    picker.close()


def test_catalog_and_group_form_support_multiple_positions_and_tags(window, store, app):
    window.tabs.setCurrentIndex(1)
    window.position_name.setText("Kỹ sư PLC")
    window.position_save_button.click()
    position = window.position_id
    assert position and not window.position_save_button.isEnabled()
    window.tabs.setCurrentIndex(2)
    window.group_name.setText("Nhóm PLC")
    window.group_url.setText("https://facebook.com/groups/plc/")
    assert not window.group_save_button.isEnabled()
    window.group_positions.set_checked([p["id"] for p in store.positions()])
    window.category.new_label.setText("Hà Nội, Tuyển gấp")
    window.category.add_labels()
    window.group_save_button.click()
    value = store.groups()[0]
    assert len(value["position_ids"]) == 2 and value["category"] == "Hà Nội, Tuyển gấp"
    assert not window.group_save_button.isEnabled()
    window.refresh_positions()
    assert not window.delete_position_action.isEnabled()
    window.resize(980, 680)
    app.processEvents()
    assert window.width() == 980
    bottom = window.group_save_button.mapTo(window, QPoint(0, window.group_save_button.height()))
    assert 0 < bottom.y() < window.height()
    window.load_group(window.group_list.item(0))
    assert set(window.group_positions.checked_data()) == set(value["position_ids"])
    assert window.category.labels() == ["Hà Nội", "Tuyển gấp"]


def test_inline_position_creation_keeps_unsaved_group_fields(window, store, monkeypatch):
    window.group_name.setText("Đang nhập")
    window.group_url.setText("https://facebook.com/groups/working/")
    window.group_notes.setPlainText("Chưa lưu")
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Nhân viên kinh doanh", True))
    window.add_position_inline()
    assert window.group_name.text() == "Đang nhập" and window.group_notes.toPlainText() == "Chưa lưu"
    assert window.group_positions.labels() == ["Nhân viên kinh doanh"]
    assert window.group_save_button.isEnabled() and not store.groups()


@pytest.mark.parametrize("mode", [2, 3])
def test_batch_multiple_filters_deduplicate_and_preserve_manual_exclusions(window, store, task_data, mode):
    posts, groups = task_data
    a = store.positions()[0]["id"]
    b = store.save_position(None, "Kế toán")
    c = store.save_position(None, "Lái xe")
    for index, group in enumerate(store.groups()):
        store.save_group(
            group["id"],
            group["name"],
            group["url"],
            ["HN, HR", "HR", "HCM"][index],
            "",
            [[a, b], [b], [c]][index],
        )
    window.refresh_posts()
    window.refresh_positions()
    window.refresh_groups()
    window.audience_mode.setCurrentIndex(mode)
    assert window.selected_group_ids() == []
    picker = window.audience_tag if mode == 2 else window.audience_positions
    picker.set_checked(["hn", "hr"] if mode == 2 else [a, b])
    assert window.selected_group_ids() == groups[:2]
    window.audience_list.item(1).setCheckState(Qt.CheckState.Unchecked)
    window.refresh_groups()
    assert window.selected_group_ids() == groups[:1]
    batch = window.create_posting_batch()
    assert [j["group_id"] for j in store.batch_jobs(batch)] == groups[:1]
    assert not window.queue_active and not window.browser.isRunning()
    assert store.batches()[0]["audience"]


def test_unsaved_position_switch_and_delete_are_guarded(window, store, monkeypatch):
    window.position_name.setText("Chưa lưu")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.new_position()
    assert window.position_name.text() == "Chưa lưu"
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    window.new_position()
    assert not window.position_name.text()
    window.position_name.setText("Xóa thử")
    window.save_position()
    position = window.position_id
    window.delete_position()
    assert all(p["id"] != position for p in store.positions()) and window.position_id is None
