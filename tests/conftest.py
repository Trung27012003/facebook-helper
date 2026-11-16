import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def store(tmp_path):
    from facebook_helper.storage import Store

    value = Store(tmp_path / "data")
    yield value
    value.close()


@pytest.fixture
def job(store):
    post_id = store.save_post(None, "Kế toán", "<p>Ứng tuyển</p>", "Ứng tuyển", "#hr", [])
    group_id = store.save_group(None, "Nhóm HR", "https://facebook.com/groups/hr-hanoi/", "HN", "")
    return store.create_job(post_id, group_id)
