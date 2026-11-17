import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .beginner import BeginnerMixin
from .browser import BrowserWorker
from .domain import STATUSES, normalize_group, post_url
from .editor import SummernoteEditor
from .manager import PostManager, send_label
from .posting import SENT, PostingMixin
from .templates import RecruitmentDialog
from .tracking import TrackingMixin
from .widgets import button, hint, row

STYLE = """
QMainWindow, QWidget { background: #f6f8fc; color: #17243a; font-size: 14px; }
QLineEdit, QTextEdit, QListWidget, QTableWidget, QComboBox, QSpinBox {
 background: white; border: 1px solid #d9e1ee; border-radius: 6px; padding: 6px;
 selection-background-color: #dbeafe; selection-color: #17243a;
}
QPushButton { background: #e8edf5; border: none; border-radius: 6px; padding: 9px 13px; }
QPushButton:hover { background: #dce6f5; }
QPushButton:disabled { color: #8b97aa; background: #edf0f5; }
QPushButton[primary="true"] { background: #2563eb; color: white; }
QPushButton[primary="true"]:hover { background: #1d4ed8; }
QPushButton[primary="true"]:disabled { background: #a9bfe9; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: #e8edf5; padding: 12px 20px; margin: 4px 4px 8px 0; border-radius: 6px; }
QTabBar::tab:selected { background: #2563eb; color: white; }
QHeaderView::section { background: #e8edf5; padding: 8px; border: none; font-weight: bold; }
QLabel#hint { color: #52647e; }
"""


def local_time(value):
    return datetime.fromisoformat(value).astimezone().strftime("%d/%m/%Y %H:%M")


class MainWindow(BeginnerMixin, TrackingMixin, PostingMixin, QMainWindow):
    def __init__(self, store):
        super().__init__()
        self.store = store
        store.recover_interrupted()
        self.post_id = None
        self.group_id = None
        self.dirty = False
        self.loading = False
        self.busy = False
        self.closing = False
        self.setWindowTitle(f"Facebook Helper {__version__} · Trợ lý tuyển dụng")
        self.resize(1280, 850)
        self.setMinimumSize(980, 680)
        self.setStyleSheet(STYLE)
        self.browser = BrowserWorker(store.root, self)
        self.browser.done.connect(self.browser_done)
        self.browser.failed.connect(self.browser_failed)
        self.browser.progress.connect(self.browser_progress)
        self.browser.finished.connect(self.browser_stopped)
        self.browser.start()
        self.browser_buttons = []
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 18)
        heading = QLabel("Facebook Helper")
        heading.setStyleSheet("font-size: 25px; font-weight: 700;")
        heading_row = row(heading)
        heading_row.addStretch()
        heading_row.addWidget(button("Tiếp tục đợt đăng", lambda: self.guard(self.resume_saved_queue)))
        heading_row.addWidget(button("Trợ giúp", lambda: self.quick_start.show()))
        layout.addLayout(heading_row)
        layout.addWidget(self.build_quick_start())
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_editor(), "Soạn bài")
        self.tabs.addTab(self.build_groups(), "Nhóm")
        self.tabs.addTab(self.build_jobs(), "Đăng bài")
        self.post_manager = PostManager(store, self)
        self.tabs.addTab(self.post_manager, "Bài đã đăng")
        self.tabs.addTab(self.build_settings(), "Cài đặt")
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)
        self.refresh_posts()
        self.refresh_groups()
        self.refresh_jobs()
        self.tabs.currentChanged.connect(lambda *_: self.post_manager.refresh())
        self.setup_tracking()
        self.setup_drafts()
        saved_batch = self.store.preference("last_batch")
        if saved_batch.isdigit():
            self.refresh_batches(int(saved_batch))
            self.refresh_jobs()
        self.statusBar().showMessage(
            f"Đã khôi phục {len(store.recovered)} lượt bị gián đoạn. Kiểm tra trước khi gửi lại."
            if store.recovered
            else "Sẵn sàng"
        )

    def guard(self, callback):
        try:
            return callback()
        except Exception as exc:
            QMessageBox.warning(self, "Không thể thực hiện", str(exc))
            return None

    def mark_dirty(self, *args):
        if not self.loading:
            self.dirty = True
            self.save_button.setText("Lưu bài *")
            if hasattr(self, "draft_timer"):
                self.draft_timer.start()

    def confirm_discard(self):
        accepted = (
            not self.dirty
            or QMessageBox.question(
                self,
                "Nội dung chưa lưu",
                "Bỏ các thay đổi chưa lưu?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )
        if accepted:
            self.clear_active_draft()
        return accepted

    def build_editor(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        split = QSplitter()
        sidebar = QWidget()
        side = QVBoxLayout(sidebar)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm bài theo tên hoặc nội dung…")
        self.search.textChanged.connect(self.filter_posts)
        side.addWidget(self.search)
        self.post_list = QListWidget()
        self.post_list.itemClicked.connect(self.load_post)
        side.addWidget(self.post_list)
        side.addLayout(row(button("+ Bài mới", self.new_post, True), button("Nhân bản", self.duplicate_post)))
        side.addWidget(button("Tạo bài theo mẫu tuyển dụng", self.create_from_template, True))
        side.addWidget(button("Xóa bài đang mở", self.delete_post))
        split.addWidget(sidebar)
        editor = QWidget()
        main = QVBoxLayout(editor)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Tên quản lý bài · ví dụ: Kế toán — Quận 7")
        self.title.textChanged.connect(self.mark_dirty)
        self.draft_recovery = QWidget()
        recovery = QVBoxLayout(self.draft_recovery)
        self.draft_recovery_text = hint("")
        recovery.addWidget(self.draft_recovery_text)
        recovery.addLayout(
            row(
                button("Khôi phục bản nháp", lambda: self.guard(self.recover_draft), True),
                button("Bỏ các bản nháp cũ", self.discard_recovery_drafts),
            )
        )
        main.addWidget(self.draft_recovery)
        main.addWidget(self.title)
        self.content = SummernoteEditor()
        self.content.notice = lambda message: self.statusBar().showMessage(message, 15000)
        self.content.setPlaceholderText("Vị trí tuyển dụng, mức lương, yêu cầu, quyền lợi, cách ứng tuyển…")
        self.content.textChanged.connect(self.mark_dirty)
        main.addWidget(self.content, 1)
        main.addWidget(
            hint(
                "Dán từ Word hoặc Facebook bằng Ctrl+V. Ứng dụng bỏ nền tối; Facebook có thể thay đổi kiểu chữ khi đăng."
            )
        )
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("Hashtag cuối bài · #tuyendung #ketoan")
        self.tags.textChanged.connect(self.mark_dirty)
        main.addWidget(self.tags)
        self.images = QListWidget()
        self.images.setMaximumHeight(130)
        self.images.setIconSize(QSize(48, 48))
        main.addWidget(self.images)
        main.addLayout(
            row(
                button("Thêm ảnh", self.add_images),
                button("Bỏ ảnh", self.remove_image),
                button("Đưa ảnh lên", lambda: self.move_image(-1)),
                button("Đưa ảnh xuống", lambda: self.move_image(1)),
                button("Mở ảnh", self.open_image),
            )
        )
        self.autosave_note = hint("Bản đang soạn được tự lưu sau khi bạn ngừng nhập một lúc.")
        main.addWidget(self.autosave_note)
        self.save_button = button("Lưu bài", lambda: self.guard(self.save_post))
        main.addLayout(
            row(
                self.save_button,
                button("Đăng bài này", lambda: self.guard(self.post_this_article), True),
                button("Xem trước bài", self.preview_article),
                button("Sao chép bài có định dạng", self.copy_editor),
            )
        )
        split.addWidget(editor)
        split.setSizes([310, 850])
        layout.addWidget(split)
        return page

    def create_from_template(self):
        if (self.dirty or self.content.toPlainText().strip()) and not self.confirm_template_replace():
            return
        dialog = RecruitmentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.post_id = None
        self.images.clear()
        self.title.setText(dialog.article["title"])
        self.content.setHtml(dialog.article["html"])
        self.tags.setText(dialog.article["tags"])
        self.mark_dirty()
        self.statusBar().showMessage("Đã tạo nội dung. Thêm ảnh, xem trước rồi bấm Lưu bài nhé.", 15000)

    def confirm_template_replace(self):
        return (
            QMessageBox.question(
                self,
                "Tạo bài theo mẫu",
                "Tạo nội dung mới thay cho bản đang mở? Hãy lưu bài cũ trước nếu cần giữ lại.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def preview_article(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Xem trước nội dung tuyển dụng")
        dialog.resize(680, 760)
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            hint(
                "Bố cục bản nháp. Khi đăng, Facebook quyết định kiểu chữ và cách hiển thị ảnh. Nội dung chữ vẫn giữ tiêu đề và các dòng •."
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        content = QVBoxLayout(body)
        text = QTextEdit()
        text.setReadOnly(True)
        from html import escape

        text.setHtml(self.content.toHtml() + "<p style='color:#2563eb'>" + escape(self.tags.text()) + "</p>")
        text.setMinimumHeight(350)
        content.addWidget(text)
        from PySide6.QtGui import QPixmap

        for index in range(self.images.count()):
            relative = self.images.item(index).data(Qt.ItemDataRole.UserRole)
            image = QLabel()
            image.setPixmap(
                QPixmap(str(self.store.asset(relative))).scaledToWidth(
                    570, Qt.TransformationMode.SmoothTransformation
                )
            )
            content.addWidget(image)
        scroll.setWidget(body)
        layout.addWidget(scroll)
        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        actions.button(QDialogButtonBox.StandardButton.Close).setText("Đóng xem trước")
        actions.rejected.connect(dialog.reject)
        layout.addWidget(actions)
        dialog.exec()

    def refresh_posts(self):
        self.post_list.clear()
        for post in self.store.posts():
            item = QListWidgetItem(post["title"])
            item.setData(Qt.ItemDataRole.UserRole, post["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, post["plain"] + "\n" + post["tags"])
            item.setToolTip(post["plain"][:250])
            self.post_list.addItem(item)
        self.filter_posts()
        self.refresh_post_choices()

    def filter_posts(self):
        query = self.search.text().casefold()
        for index in range(self.post_list.count()):
            item = self.post_list.item(index)
            item.setHidden(
                query not in (item.text() + " " + (item.data(Qt.ItemDataRole.UserRole + 1) or "")).casefold()
            )

    def load_post(self, item):
        if not self.confirm_discard():
            return
        post = self.store.post(item.data(Qt.ItemDataRole.UserRole))
        self.loading = True
        self.post_id = post["id"]
        self.title.setText(post["title"])
        self.content.setHtml(post["html"])
        self.tags.setText(post["tags"])
        self.images.clear()
        for image in post["images"]:
            self.add_image_item(image)
        self.loading = False
        self.dirty = False
        self.save_button.setText("Lưu bài")

    def new_post(self):
        if not self.confirm_discard():
            return
        self.loading = True
        self.post_id = None
        self.title.clear()
        self.content.clear()
        self.tags.clear()
        self.images.clear()
        self.loading = False
        self.dirty = False
        self.save_button.setText("Lưu bài")
        self.title.setFocus()

    def duplicate_post(self):
        self.post_id = None
        self.title.setText(self.title.text() + " (bản sao)")
        self.mark_dirty()

    def save_post(self):
        images = [self.images.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.images.count())]
        self.post_id = self.store.save_post(
            self.post_id,
            self.title.text(),
            self.content.toHtml(),
            self.content.toPlainText(),
            self.tags.text(),
            images,
        )
        self.dirty = False
        self.clear_active_draft()
        self.save_button.setText("Lưu bài")
        self.refresh_posts()
        self.statusBar().showMessage("Đã lưu bài viết", 5000)
        return self.post_id

    def delete_post(self):
        if self.post_id is None:
            return
        if (
            QMessageBox.question(self, "Xóa bài", "Xóa bài đang mở? Lịch sử đăng vẫn được giữ.")
            == QMessageBox.StandardButton.Yes
        ):
            self.store.delete_post(self.post_id)
            self.dirty = False
            self.new_post()
            self.refresh_posts()

    def add_image_item(self, image):
        path = self.store.root / image
        item = QListWidgetItem(QIcon(str(path)), path.name)
        item.setData(Qt.ItemDataRole.UserRole, image)
        item.setToolTip(str(path))
        self.images.addItem(item)
        self.renumber_images()

    def renumber_images(self):
        for i in range(self.images.count()):
            self.images.item(i).setText(f"Ảnh {i + 1}")

    def add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Chọn ảnh", "", "Ảnh (*.jpg *.jpeg *.png *.webp)")
        for path in paths:
            image = self.guard(lambda p=path: self.store.import_image(p))
            if image:
                self.add_image_item(image)
                self.mark_dirty()

    def remove_image(self):
        index = self.images.currentRow()
        if index >= 0:
            self.images.takeItem(index)
            self.renumber_images()
            self.mark_dirty()

    def move_image(self, delta):
        index = self.images.currentRow()
        target = index + delta
        if index >= 0 and 0 <= target < self.images.count():
            item = self.images.takeItem(index)
            self.images.insertItem(target, item)
            self.images.setCurrentRow(target)
            self.renumber_images()
            self.mark_dirty()

    def open_image(self):
        item = self.images.currentItem()
        if item:
            self.open_local(item.data(Qt.ItemDataRole.UserRole))

    def copy_editor(self):
        self.content.copy_article(self.tags.text())
        self.statusBar().showMessage(
            "Đã sao chép cả định dạng và chữ thuần. Nơi nhận quyết định định dạng hỗ trợ.", 10000
        )

    def build_groups(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        self.group_list = QListWidget()
        self.group_list.itemClicked.connect(self.load_group)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("Tìm nhóm theo tên hoặc nhãn…")
        self.group_search.textChanged.connect(self.filter_group_list)
        sidebar_layout.addWidget(self.group_search)
        sidebar_layout.addWidget(self.group_list)
        layout.addWidget(sidebar, 1)
        form_widget = QWidget()
        form = QVBoxLayout(form_widget)
        fields = QFormLayout()
        self.group_name = QLineEdit()
        self.group_url = QLineEdit()
        self.group_url.setPlaceholderText("https://www.facebook.com/groups/…/")
        self.category = QLineEdit()
        self.category.setPlaceholderText("Ví dụ: Hà Nội, Kỹ thuật, Tuyển gấp")
        self.group_notes = QTextEdit()
        self.group_notes.setAcceptRichText(False)
        self.group_notes.setPlaceholderText("Quy định nhóm, khung giờ, thông tin cần lưu ý…")
        fields.addRow("Tên nhóm", self.group_name)
        fields.addRow("Link nhóm", self.group_url)
        fields.addRow("Nhãn nhóm", self.category)
        fields.addRow("Ghi chú", self.group_notes)
        form.addLayout(fields)
        form.addLayout(
            row(
                button("+ Nhóm mới", self.new_group),
                button("Lưu nhóm", lambda: self.guard(self.save_group), True),
                button("Xóa nhóm", self.delete_group),
            )
        )
        form.addWidget(
            hint(
                "Nhiều nhóm có thể dùng cùng nhãn. Ngăn cách các nhãn bằng dấu phẩy, ví dụ: Hà Nội, Kỹ thuật. Nhãn dùng để chọn nơi đăng; không được đưa vào bài Facebook."
            )
        )
        layout.addWidget(form_widget, 2)
        return page

    def refresh_groups(self):
        current = self.job_groups.currentData()
        self.group_list.clear()
        self.job_groups.clear()
        for group in self.store.groups():
            item = QListWidgetItem(group["name"] + (f" · {group['category']}" if group["category"] else ""))
            item.setData(Qt.ItemDataRole.UserRole, group)
            self.group_list.addItem(item)
            self.job_groups.addItem(group["name"], group["id"])
        index = self.job_groups.findData(current)
        if index >= 0:
            self.job_groups.setCurrentIndex(index)
        self.refresh_audience_tags()
        self.filter_group_list()

    def filter_group_list(self):
        query = self.group_search.text().casefold()
        for index in range(self.group_list.count()):
            item = self.group_list.item(index)
            item.setHidden(query not in item.text().casefold())

    def load_group(self, item):
        if not self.confirm_group_switch():
            return
        group = item.data(Qt.ItemDataRole.UserRole)
        self.group_id = group["id"]
        self.group_name.setText(group["name"])
        self.group_url.setText(group["url"])
        self.category.setText(group["category"])
        self.group_notes.setPlainText(group["notes"])
        self.group_original = self.group_values()

    def group_values(self):
        return (
            self.group_name.text(),
            self.group_url.text(),
            self.category.text(),
            self.group_notes.toPlainText(),
        )

    def confirm_group_switch(self):
        values = self.group_values()
        original = getattr(self, "group_original", ("", "", "", ""))
        return (
            values == original
            or QMessageBox.question(
                self,
                "Nhóm chưa lưu",
                "Bỏ các thay đổi chưa lưu của nhóm?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def new_group(self):
        if not self.confirm_group_switch():
            return
        self.group_id = None
        for field in (self.group_name, self.group_url, self.category, self.group_notes):
            field.clear()
        self.group_original = self.group_values()

    def save_group(self):
        self.group_id = self.store.save_group(self.group_id, *self.group_values())
        self.group_original = self.group_values()
        self.refresh_groups()
        self.statusBar().showMessage("Đã lưu nhóm", 5000)

    def delete_group(self):
        if (
            self.group_id is not None
            and QMessageBox.question(self, "Xóa nhóm", "Xóa nhóm này? Lịch sử đăng vẫn được giữ.")
            == QMessageBox.StandardButton.Yes
        ):
            self.store.delete_group(self.group_id)
            self.group_original = self.group_values()
            self.new_group()
            self.refresh_groups()

    def build_jobs(self):
        container = QWidget()
        outer = QVBoxLayout(container)
        page = QWidget()
        layout = QVBoxLayout(page)
        self.build_audience(layout)
        layout = self.run_layout
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Tìm bài hoặc nhóm trong đợt…")
        self.history_search.textChanged.connect(self.filter_jobs)
        layout.addWidget(self.history_search)
        self.history = QTableWidget(0, 6)
        self.history.setHorizontalHeaderLabels(
            ["Mã", "Bài tuyển dụng", "Nhóm", "Trạng thái", "Cập nhật", "Link bài"]
        )
        self.history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history.itemSelectionChanged.connect(self.load_job)
        self.history.setColumnHidden(0, True)
        self.history.setColumnHidden(4, True)
        self.history.setMinimumHeight(120)
        self.history.verticalHeader().hide()
        layout.addWidget(self.history, 1)
        self.job_detail = hint("Chọn một lượt đăng để thao tác.")
        self.extra_tools = QWidget()
        toggle = button("Chi tiết", lambda: None)
        toggle.setCheckable(True)
        toggle.toggled.connect(self.extra_tools.setVisible)
        self.result_open_button = button("Mở bài", self.open_selected_post)
        self.result_copy_button = button("Sao chép link", self.copy_link)
        self.result_group_button = button("Mở nhóm", self.open_selected_group)
        result_actions = row(self.result_open_button, self.result_copy_button, self.result_group_button)
        result_actions.addStretch()
        result_actions.addWidget(toggle)
        layout.addLayout(result_actions)
        layout.addWidget(self.extra_tools)
        layout = QVBoxLayout(self.extra_tools)
        layout.addWidget(self.job_detail)
        self.extra_tools.hide()
        self.link = QLineEdit()
        self.link.setPlaceholderText("Dán link bài cụ thể: https://www.facebook.com/groups/…/posts/…/")
        layout.addLayout(
            row(
                self.link,
                button("Lưu link", lambda: self.guard(self.save_link)),
                button("Copy link", self.copy_link),
            )
        )
        self.status_choice = QComboBox()
        for key, value in STATUSES.items():
            self.status_choice.addItem(value, key)
        self.job_note = QLineEdit()
        self.job_note.setPlaceholderText("Ghi chú kết quả đăng / lý do từ chối")
        layout.addLayout(
            row(
                self.status_choice,
                self.job_note,
                button("Lưu trạng thái & ghi chú", lambda: self.guard(self.save_status)),
            )
        )
        layout.addLayout(
            row(
                self.browser_button("Mở nhóm", "open_group"),
                button("Sao chép bài", self.copy_job),
                button("Mở thư mục ảnh", self.open_job_images),
            )
        )
        layout.addLayout(
            row(
                self.browser_button("Lấy link đang mở", "read_link"),
                self.browser_button("Mở link bài", "capture"),
                self.browser_button("Chụp màn hình", "screenshot"),
                button("Xem ảnh minh chứng", self.open_evidence),
                button("Xuất Excel", self.export_excel),
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        outer.addWidget(scroll, 1)
        outer.addLayout(self.posting_navigation)
        return container

    def refresh_post_choices(self):
        current = self.job_posts.currentData()
        self.job_posts.clear()
        for post in self.store.posts():
            self.job_posts.addItem(post["title"], post["id"])
        index = self.job_posts.findData(current)
        if index >= 0:
            self.job_posts.setCurrentIndex(index)

    def create_job(self):
        post_id, group_id = self.job_posts.currentData(), self.job_groups.currentData()
        if post_id is None or group_id is None:
            raise ValueError("Cần lưu ít nhất một bài viết và một nhóm trước.")
        if self.dirty and self.post_id == post_id:
            raise ValueError("Bài đang có thay đổi chưa lưu. Hãy lưu trước khi tạo lượt đăng.")
        previous = self.store.post_duplicates(post_id, [group_id])
        if (
            previous
            and QMessageBox.question(
                self,
                "Cảnh báo trùng nội dung",
                "Nội dung và ảnh này đã có lượt trong nhóm. Vẫn tạo lượt mới để đăng lại?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        job_id = self.store.create_job(post_id, group_id, allow_duplicate=bool(previous))
        self.refresh_jobs(job_id)

    def current_job(self):
        selected = self.history.currentRow()
        if selected < 0 or self.history.isRowHidden(selected) or not self.history.item(selected, 0):
            raise ValueError("Chọn một lượt đăng trong bảng trước.")
        return self.store.job(int(self.history.item(selected, 0).text()))

    def refresh_jobs(self, selected_id=None):
        if selected_id is None:
            try:
                selected_id = self.current_job()["id"]
            except ValueError:
                pass
        self.history.blockSignals(True)
        jobs = self.store.jobs()
        active_batch = self.batch_filter.currentData()
        if active_batch is not None:
            jobs.sort(
                key=lambda job: (
                    job["batch_id"] != active_batch,
                    job["position"] if job["batch_id"] == active_batch else -job["id"],
                )
            )
        self.history.setRowCount(len(jobs))
        selected_row = -1
        for index, job in enumerate(jobs):
            for col, value in enumerate(
                (
                    job["id"],
                    job["title"],
                    job["group_name"],
                    send_label(job),
                    local_time(job["updated_at"]),
                    job["url"],
                )
            ):
                item = QTableWidgetItem(str(value) if col != 5 or value else "Chưa có link")
                item.setToolTip(item.text())
                if col == 3:
                    item.setForeground(
                        QColor(
                            "#166534"
                            if job["status"] in SENT
                            else "#92400e"
                            if job["status"] in {"error", "uncertain"}
                            else "#334155"
                        )
                    )
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, job["batch_id"])
                self.history.setItem(index, col, item)
            if job["id"] == selected_id:
                selected_row = index
        self.history.blockSignals(False)
        self.refresh_batches()
        self.filter_jobs()
        if selected_row < 0 or self.history.isRowHidden(selected_row):
            selected_row = next(
                (index for index in range(self.history.rowCount()) if not self.history.isRowHidden(index)), -1
            )
        if selected_row >= 0:
            self.history.selectRow(selected_row)
            self.load_job()
        else:
            self.history.clearSelection()
            self.history.setCurrentCell(-1, -1)
            self.link.clear()
            self.job_note.clear()
            self.job_detail.clear()
            self.result_open_button.setEnabled(False)
            self.result_copy_button.setEnabled(False)
            self.result_group_button.setEnabled(False)

    def filter_jobs(self):
        query = self.history_search.text().casefold()
        for index in range(self.history.rowCount()):
            text = " ".join(self.history.item(index, col).text() for col in range(self.history.columnCount()))
            batch_id = self.batch_filter.currentData()
            matches_batch = (
                batch_id is None or self.history.item(index, 0).data(Qt.ItemDataRole.UserRole) == batch_id
            )
            self.history.setRowHidden(index, not matches_batch or query not in text.casefold())
        if hasattr(self, "result_group_button"):
            try:
                current = self.current_job()
            except ValueError:
                current = None
            self.result_group_button.setEnabled(bool(current))
            self.result_open_button.setEnabled(bool(current and current["url"]))
            self.result_copy_button.setEnabled(bool(current and current["url"]))

    def load_job(self):
        try:
            job = self.current_job()
        except ValueError:
            return
        self.link.setText(job["url"])
        self.status_choice.setCurrentIndex(self.status_choice.findData(job["status"]))
        self.job_note.setText(job["note"])
        self.job_detail.setText(
            f"{job['title']} · {job['group_name']} · {len(json.loads(job['images']))} ảnh"
        )
        self.result_open_button.setEnabled(bool(job["url"]))
        self.result_copy_button.setEnabled(bool(job["url"]))
        self.result_group_button.setEnabled(True)

    def open_selected_group(self):
        job = self.current_job()
        QDesktopServices.openUrl(QUrl(normalize_group(job["group_url"])))

    def open_selected_post(self):
        job = self.current_job()
        if job["url"]:
            QDesktopServices.openUrl(QUrl(job["url"]))

    def save_link(self):
        if self.queue_active and self.queue_auto:
            self.pause_posting_queue(announce=False)
        job = self.current_job()
        self.store.update_job(job["id"], url=self.link.text().strip())
        self.refresh_jobs(job["id"])

    def copy_link(self):
        def action():
            job = self.current_job()
            if not job["url"]:
                raise ValueError("Chưa lưu link bài đăng.")
            QApplication.clipboard().setText(job["url"])
            self.statusBar().showMessage("Đã sao chép link", 5000)

        self.guard(action)

    def save_status(self):
        if self.busy or self.monitor_running:
            raise ValueError("Chờ thao tác trình duyệt hoàn tất trước khi sửa trạng thái.")
        if self.queue_active and self.queue_auto:
            self.pause_posting_queue(announce=False)
        job = self.current_job()
        status = self.status_choice.currentData()
        url = self.link.text().strip()
        if url:
            url = post_url(url, job["group_url"])
        if status == "published" and (job["status"] != "published" or url != job["url"]):
            if (
                QMessageBox.question(
                    self,
                    "Xác nhận bài đã hiển thị",
                    "Bạn đã mở link và thấy bài hiển thị trong nhóm?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
        self.store.update_job(job["id"], status=status, note=self.job_note.text(), url=url)
        self.refresh_jobs(job["id"])

    def copy_job(self):
        self.guard(lambda: QApplication.clipboard().setText(self.current_job()["body"]))

    def open_job_images(self):
        def action():
            job = self.current_job()
            images = json.loads(job["images"])
            if not images:
                raise ValueError("Lượt đăng này không có ảnh.")
            # Export only this job's images, named in their intended upload order.
            import shutil
            import tempfile

            folder = Path(tempfile.mkdtemp(prefix="facebook-helper-images-"))
            for index, image in enumerate(images, 1):
                source = self.store.asset(image)
                shutil.copy2(source, folder / f"{index:02d}{source.suffix}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

        self.guard(action)

    def open_local(self, relative):
        self.guard(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.asset(relative)))))

    def open_evidence(self):
        def action():
            evidence = self.current_job()["evidence"]
            if not evidence:
                raise ValueError("Chưa có ảnh minh chứng.")
            self.open_local(evidence)

        self.guard(action)

    def browser_button(self, label, action):
        widget = button(label, lambda: self.guard(lambda: self.run_browser(action)))
        self.browser_buttons.append(widget)
        return widget

    def run_browser(self, action):
        if self.monitor_running:
            raise ValueError("Bấm Dừng kiểm tra và chờ bài đang đọc hoàn tất trước khi thao tác trình duyệt.")
        if action == "login" and self.queue_active:
            self.pause_posting_queue(announce=False)
        if self.queue_active and self.queue_auto and not self.queue_dispatching and action != "login":
            raise ValueError("Bấm Tạm dừng trước khi thao tác một lượt khác bằng tay.")
        if self.busy:
            raise ValueError("Chờ thao tác trình duyệt hiện tại hoàn tất.")
        payload = {}
        if action != "login":
            job = self.current_job()
            if self.link.text().strip() != job["url"] and action in {"capture", "screenshot"}:
                raise ValueError("Hãy lưu link bài trước.")
            payload = {
                **job,
                "job_id": job["id"],
                "images": [str(self.store.asset(p)) for p in json.loads(job["images"])],
            }
            if action in {"capture", "screenshot"} and not job["url"]:
                raise ValueError("Hãy lưu link bài cụ thể trước.")
        if action in {"publish", "publish_current"}:
            if job["status"] in SENT:
                raise ValueError(
                    "Lượt này đã được xử lý. Nếu muốn đăng lại, hãy tạo lượt mới và xác nhận cảnh báo trùng."
                )
            if job["status"] in {"sending", "uncertain"}:
                raise ValueError(
                    "Lượt này chưa rõ kết quả. Kiểm tra Facebook trước khi gửi lại để tránh trùng."
                )
            if not job["allow_duplicate"] and self.store.duplicates(
                job["body"],
                json.loads(job["images"]),
                [job["group_url"]],
                exclude_id=job["id"],
                sent_only=True,
            ):
                raise ValueError(
                    "Đã có lượt cùng nội dung và ảnh được gửi hoặc chưa rõ kết quả trong nhóm. Xem lại bài đã gửi; nếu muốn đăng lại hãy tạo danh sách mới và xác nhận cảnh báo trùng."
                )
            self.store.update_job(payload["job_id"], source="browser", status="sending")
        self.busy = True
        for widget in self.browser_buttons:
            widget.setEnabled(False)
        self.update_queue_progress()
        self.browser.submit(action, payload)

    def browser_progress(self, message):
        if message:
            job = getattr(self, "queue_current_job", None)
            prefix = (
                f"Nhóm {job['position'] + 1}/{self.queue_current_total}: {job['group_name']}\n"
                if self.queue_active and job
                else ""
            )
            self.current_action.setText(prefix + message)
            self.statusBar().showMessage(message)

    def finish_browser(self):
        self.busy = False
        for widget in self.browser_buttons:
            widget.setEnabled(True)
        self.update_queue_progress()

    def browser_done(self, action, result):
        self.finish_browser()
        if action == "check_status":
            if not self.guard(lambda: (self.complete_check(result), True)[1]):
                self.stop_checks()
            return

        def save():
            if action == "fill" or (
                action in {"prepare", "publish", "publish_current"} and result.get("filled")
            ):
                job = self.store.job(result["job_id"])
                if job["status"] in {"draft", "error", "sending"}:
                    self.store.update_job(job["id"], status="prepared")
            if action in {"publish", "publish_current"}:
                status = (
                    "uncertain" if result.get("uncertain") else "submitted" if result.get("sent") else "error"
                )
                if self.store.job(result["job_id"])["status"] not in SENT:
                    self.store.update_job(
                        result["job_id"],
                        source="browser",
                        status=result["status"]
                        if result.get("sent")
                        and not result.get("uncertain")
                        and result.get("status") in {"submitted", "pending", "published"}
                        else status,
                        note=result.get("message", ""),
                        **(
                            {"url": result["url"]}
                            if (result.get("sent") or result.get("link_captured")) and result.get("url")
                            else {}
                        ),
                    )
            if action == "read_link":
                self.store.update_job(result["job_id"], url=result["url"])
            if action == "screenshot":
                job = self.store.job(result["job_id"])
                if post_url(result["url"], job["group_url"]) != job["url"]:
                    raise ValueError("Link bài đã thay đổi trong khi chụp. Hãy mở link mới và chụp lại.")
                self.store.update_job(result["job_id"], evidence=result["evidence"])
            self.refresh_jobs()
            self.post_manager.refresh()
            return True

        if self.guard(save):
            self.current_action.setText(result["message"])
            self.statusBar().showMessage(result["message"], 20000)
            self.queue_browser_done(action, result)
        else:
            self.pause_posting_queue(announce=False)
            self.statusBar().showMessage("Chưa lưu được kết quả. Kiểm tra thông báo và thử lại.", 15000)

    def browser_failed(self, action, message, payload):
        self.finish_browser()
        if action == "check_status":
            self.stop_checks()
            self.guard(lambda: self.complete_check({**payload, "outcome": "unknown", "message": message}))
            return
        self.pause_posting_queue(announce=False)
        if action in {"publish", "publish_current", "prepare", "fill"}:
            self.pause_posting_queue(announce=False)
            if payload.get("job_id"):
                self.store.update_job(
                    payload["job_id"],
                    status="uncertain" if payload.get("submission_started") else "error",
                    note=message,
                )
                self.refresh_jobs()
        self.statusBar().showMessage("Thao tác trình duyệt chưa hoàn tất", 15000)
        if payload.get("submission_started"):
            help_text = (
                "Chưa rõ bài đã gửi hay chưa. Mở nhóm để kiểm tra trước khi thử lại, tránh đăng trùng."
            )
        elif any(word in message.casefold() for word in ("đăng nhập", "login", "checkpoint", "xác thực")):
            help_text = (
                "Facebook cần đăng nhập hoặc xác thực. Bấm Mở Facebook để xử lý, rồi quay lại Tiếp tục."
            )
        elif any(word in message.casefold() for word in ("blocked", "hạn chế", "bị chặn")):
            help_text = (
                "Facebook đang hạn chế thao tác. Kiểm tra thông báo trong Facebook trước khi tiếp tục."
            )
        else:
            help_text = "Chưa hoàn tất thao tác. Kiểm tra kết nối mạng và cửa sổ Facebook. Đợt đăng đã tạm dừng; các nhóm còn lại được giữ."
        self.problem_help.setText(help_text)
        self.problem_details.setPlainText(message)
        self.problem_panel.show()
        self.current_action.setText(help_text)
        QMessageBox.warning(self, "Cần bạn kiểm tra", help_text)

    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất báo cáo", "bao-cao-tuyen-dung.xlsx", "Excel (*.xlsx)"
        )
        if path:
            result = self.guard(lambda: (self.store.export_excel(path), True)[1])
            if result:
                self.statusBar().showMessage("Đã xuất báo cáo Excel", 5000)

    def build_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        guide = QTextEdit()
        guide.setReadOnly(True)
        guide.setHtml("""
        <h3>Cách sử dụng</h3>
        <p>1. Đăng nhập Facebook từ nút Trợ giúp ở đầu cửa sổ.</p>
        <p>2. Thêm nhóm trong tab Nhóm, soạn và lưu bài trong Soạn bài.</p>
        <p>3. Vào Đăng bài, chọn bài và nhóm, xem lại rồi Bắt đầu đăng.</p>
        <p>4. Vào Bài đã đăng, chọn đợt và khoảng ngày rồi bấm Tìm kiếm.
        Chọn một dòng để mở bài hoặc sao chép link. Xuất Excel lấy toàn bộ kết quả tìm kiếm.</p>
        <h3>Lưu kết quả</h3>
        <p>Sau khi gửi, ứng dụng lưu kết quả và link nếu Facebook trả về, rồi chuyển nhóm.
        Không chờ duyệt. Nếu chưa rõ đã gửi hay chưa, ứng dụng dừng để tránh đăng trùng.</p>
        <p>Nội dung đang soạn được tự lưu thành nháp; bấm Lưu bài để dùng đăng.
        Dùng Tiếp tục đợt đăng để mở công việc còn lại sau khi khởi động lại.</p>
        <h3>Dữ liệu</h3>
        <p>Sao lưu trước khi đổi máy hoặc khôi phục dữ liệu. Bản sao lưu không chứa phiên Facebook;
        máy mới cần đăng nhập lại. Đóng ứng dụng trước khi khôi phục.</p>
        """)
        layout.addWidget(guide)
        location = QLineEdit(str(self.store.root))
        location.setReadOnly(True)
        layout.addWidget(location)
        layout.addLayout(
            row(
                button(
                    "Mở thư mục dữ liệu",
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.root))),
                ),
                button("Sao lưu ZIP", self.backup),
            )
        )
        return page

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Sao lưu dữ liệu", "facebook-helper-backup.zip", "ZIP (*.zip)"
        )
        if path:
            result = self.guard(lambda: (self.store.backup(path), True)[1])
            if result:
                self.statusBar().showMessage("Đã sao lưu dữ liệu (không gồm phiên Facebook)", 10000)

    def browser_stopped(self):
        # finished can arrive before native thread cleanup completes.
        self.browser.wait()
        if self.closing:
            self.close()

    def closeEvent(self, event):
        self.monitor_timer.stop()
        self.stop_checks()
        self.pause_posting_queue(announce=False)
        if self.closing:
            if self.browser.isRunning():
                event.ignore()
            else:
                event.accept()
            return
        if self.dirty and not self.autosave_draft():
            self.configure_tracking()
            QMessageBox.warning(
                self,
                "Chưa lưu được bản nháp",
                "Ứng dụng chưa đóng để tránh mất nội dung. Hãy Lưu bài hoặc kiểm tra ổ đĩa.",
            )
            event.ignore()
            return
        self.draft_timer.stop()
        if not self.confirm_group_switch():
            self.configure_tracking()
            event.ignore()
            return
        self.dirty = False
        self.group_original = self.group_values()
        if self.browser.isRunning():
            # Do not destroy a running QThread; shutdown is asynchronous even during navigation.
            self.closing = True
            self.setEnabled(False)
            self.statusBar().showMessage("Đang đóng trình duyệt, vui lòng chờ…")
            self.browser.submit("stop")
            event.ignore()
            return
        event.accept()
