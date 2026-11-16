import time

from PySide6.QtCore import QCoreApplication, QElapsedTimer, QEvent
from PySide6.QtGui import QFont

from facebook_helper.ui import MainWindow


def test_editor_groups_history_and_shutdown(app, store):
    window = MainWindow(store)
    try:
        window.show()
        app.processEvents()
        assert window.tabs.count() == 4
        window.title.setText("Nhân viên kinh doanh")
        window.content.setPlainText("Ứng tuyển ngay\nLương thỏa thuận")
        window.content.selectAll()
        window.bold.setChecked(True)
        window.toggle_bold()
        window.change_size(18)
        window.tags.setText("#tuyendung")
        assert window.dirty
        post_id = window.save_post()
        assert "font-weight:700" in store.post(post_id)["html"]
        assert window.content.currentCharFormat().fontWeight() == QFont.Weight.Bold
        assert not window.dirty
        window.group_name.setText("Việc làm Hà Nội")
        window.group_url.setText("https://facebook.com/groups/hr-hanoi/")
        window.save_group()
        window.create_job()
        assert window.history.rowCount() == 1
        job_id = window.current_job()["id"]
        assert window.current_job()["body"].endswith("#tuyendung")
        window.link.setText("https://facebook.com/groups/hr-hanoi/posts/456/")
        window.save_link()
        window.status_choice.setCurrentIndex(window.status_choice.findData("pending"))
        window.save_status()
        assert store.job(job_id)["status"] == "pending"
        window.copy_link()
        assert app.clipboard().text().endswith("/posts/456/")
        window.new_post()
        window.load_post(window.post_list.item(0))
        assert window.content.toPlainText() == "Ứng tuyển ngay\nLương thỏa thuận"
        assert "font-weight:700" in window.content.toHtml()
        window.history_search.setText("không tồn tại")
        assert window.history.isRowHidden(0)
    finally:
        window.dirty = False
        window.group_original = window.group_values()
        window.close()
        timer = QElapsedTimer()
        timer.start()
        while window.isVisible() and timer.elapsed() < 5000:
            app.processEvents()
            time.sleep(0.02)  # release the GIL so the Python browser worker can finish
        assert not window.browser.isRunning()
        app.processEvents()
        assert not window.isVisible()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
