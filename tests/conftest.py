import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    # Offscreen Qt must release Python-owned clipboard MIME data before QApplication teardown.
    application.clipboard().clear()
    application.processEvents()


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


@pytest.fixture
def window(app, store):
    import time

    from PySide6.QtCore import QCoreApplication, QEvent

    from facebook_helper.ui import MainWindow

    value = MainWindow(store)
    value.show()
    app.processEvents()
    try:
        yield value
    finally:
        value.dirty = False
        value.group_original = value.group_values()
        value.close()
        deadline = time.monotonic() + 10
        while value.isVisible() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.02)
        assert not value.browser.isRunning(), "Browser worker did not stop"
        assert not value.isVisible(), "Window did not close"
        value.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture
def task_data(app, store, tmp_path):
    from PySide6.QtGui import QColor, QImage

    posts = []
    for index, (title, text, color) in enumerate(
        [
            ("Kế toán", "Tuyển kế toán\nLương 15 triệu", "red"),
            ("Kinh doanh", "Tuyển kinh doanh\nLương 20 triệu", "blue"),
        ]
    ):
        image = QImage(12, 12, QImage.Format.Format_RGB32)
        image.fill(QColor(color))
        source = tmp_path / f"post-{index}.png"
        assert image.save(str(source))
        relative = store.import_image(source)
        posts.append(store.save_post(None, title, f"<p>{text}</p>", text, f"#vitri{index}", [relative]))
    groups = [
        store.save_group(None, f"Nhóm {index}", f"https://facebook.com/groups/hr-{index}/", "HR", "")
        for index in range(3)
    ]
    return posts, groups
