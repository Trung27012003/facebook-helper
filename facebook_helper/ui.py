import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
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
from .choices import CheckPicker, TagPicker
from .domain import STATUSES, normalize_group, post_url
from .editor import SummernoteEditor
from .manager import PostManager, send_label
from .posting import SENT, PostingMixin
from .templates import RecruitmentDialog
from .tracking import TrackingMixin
from .updates import UpdateChecker
from .widgets import button, hint, menu_button, primary, row, toolbar

STYLE = """
QWidget { color:#17243a; font-family:"Segoe UI",sans-serif; font-size:14px; }
QMainWindow, QWidget#appRoot { background:#f5f7fb; }
QWidget#editorBody { background:white; }
QWidget#panel, QGroupBox { background:white; border:1px solid #e2e8f0; border-radius:10px; }
QGroupBox { margin-top:14px; padding:18px 12px 12px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:14px; padding:0 5px; }
QLabel#sectionTitle { font-size:17px; font-weight:600; }
QLabel#hint { color:#64748b; font-size:13px; }
QLineEdit, QTextEdit, QTextBrowser, QListWidget, QTableWidget, QComboBox, QSpinBox, QDateEdit {
 background:white; border:1px solid #dce3ee; border-radius:6px; padding:6px;
 selection-background-color:#dbeafe; selection-color:#17243a;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus { border:1px solid #2563eb; }
QLineEdit:read-only { background:#f8fafc; color:#64748b; }
QPushButton { background:white; border:1px solid #dce3ee; border-radius:6px; padding:8px 12px; }
QPushButton:hover { background:#f1f5f9; border-color:#b8c8df; }
QPushButton:focus { border:2px solid #93b4f4; }
QPushButton:disabled { color:#94a3b8; background:#f1f5f9; border-color:#e8edf5; }
QPushButton[primary="true"] { background:#2563eb; color:white; border-color:#2563eb; font-weight:600; }
QPushButton[primary="true"]:hover { background:#1d4ed8; }
QPushButton[primary="true"]:disabled { background:#dbe6fa; color:#7c96c4; border-color:#dbe6fa; }
QPushButton[danger="true"] { background:#fff7f7; color:#b91c1c; border-color:#fecaca; }
QPushButton[danger="true"]:disabled { color:#c7a5a5; border-color:#f1e2e2; }
QTabWidget::pane { border:none; }
QTabBar::tab { background:transparent; color:#64748b; padding:11px 18px; margin:4px 4px 8px 0; border-radius:6px; }
QTabBar::tab:selected { background:#dbeafe; color:#1d4ed8; font-weight:600; }
QTabBar::tab:hover { background:#e8eef8; }
QHeaderView::section { background:#f1f5f9; padding:9px; border:none; font-weight:600; }
QScrollArea { border:none; background:transparent; }
QSplitter::handle { background:transparent; width:12px; }
QProgressBar { border:none; background:#e2e8f0; border-radius:4px; }
QProgressBar::chunk { background:#2563eb; border-radius:4px; }
QMenu { background:white; border:1px solid #dce3ee; padding:5px; }
QMenu::item { padding:8px 20px; border-radius:4px; }
QMenu::item:selected { background:#dbeafe; }
"""


def local_time(value):
    return datetime.fromisoformat(value).astimezone().strftime("%d/%m/%Y %H:%M")


class MainWindow(BeginnerMixin, TrackingMixin, PostingMixin, QMainWindow):
    def __init__(self, store, background=True):
        super().__init__()
        self.store = store
        store.recover_interrupted()
        self.post_id = None
        self.group_id = None
        self.position_id = None
        self.position_original = ("", "")
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
        self.browser_buttons = []
        container = QWidget()
        container.setObjectName("appRoot")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 18, 22, 18)
        heading = QLabel("Facebook Helper")
        heading.setStyleSheet("font-size: 25px; font-weight: 700;")
        heading_row = row(heading)
        heading_row.addStretch()
        self.resume_button = button("Tiếp tục đợt đăng", lambda: self.guard(self.resume_saved_queue))
        heading_row.addWidget(self.resume_button)
        heading_row.addWidget(button("Trợ giúp", lambda: self.quick_start.show()))
        layout.addLayout(heading_row)
        layout.addWidget(self.build_quick_start())
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_editor(), "Soạn bài")
        self.tabs.addTab(self.build_positions(), "Vị trí")
        self.tabs.addTab(self.build_groups(), "Nhóm")
        self.tabs.addTab(self.build_jobs(), "Đăng bài")
        self.post_manager = PostManager(store, self)
        self.tabs.addTab(self.post_manager, "Bài đã đăng")
        self.tabs.addTab(self.build_settings(), "Cài đặt")
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)
        self.refresh_positions()
        self.refresh_posts()
        self.refresh_groups()
        self.refresh_jobs()
        self.tabs.currentChanged.connect(lambda *_: self.post_manager.refresh())
        self.setup_tracking()
        self.setup_drafts()
        self.setup_updates(background)
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
            if hasattr(self, "autosave_note"):
                self.autosave_note.setText("Chưa lưu thay đổi")
            self.update_editor_actions()
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
        sidebar.setObjectName("panel")
        sidebar.setMinimumWidth(210)
        sidebar.setMaximumWidth(330)
        side = QVBoxLayout(sidebar)
        library_title = QLabel("Bài viết")
        library_title.setObjectName("sectionTitle")
        side.addWidget(library_title)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm bài theo tên hoặc nội dung…")
        self.search.textChanged.connect(self.filter_posts)
        side.addWidget(self.search)
        self.post_list = QListWidget()
        self.post_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.post_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.post_list.itemClicked.connect(self.load_post)
        side.addWidget(self.post_list)
        self.new_post_button = button("Bài mới", self.new_post)
        self.template_button = button("Từ mẫu", self.create_from_template)
        side.addLayout(row(self.new_post_button, self.template_button))
        self.article_menu = menu_button("Thao tác bài")
        self.duplicate_action = self.article_menu.menu().addAction("Nhân bản", self.duplicate_post)
        self.copy_article_action = self.article_menu.menu().addAction(
            "Sao chép có định dạng", self.copy_editor
        )
        self.delete_article_action = self.article_menu.menu().addAction("Xóa bài đang mở", self.delete_post)
        side.addLayout(toolbar(self.article_menu))
        split.addWidget(sidebar)
        editor = QWidget()
        editor.setObjectName("panel")
        editor_outer = QVBoxLayout(editor)
        editor_body = QWidget()
        editor_body.setObjectName("editorBody")
        main = QVBoxLayout(editor_body)
        main.setContentsMargins(0, 0, 0, 0)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Tên quản lý bài · ví dụ: Kế toán — Quận 7")
        self.title.textChanged.connect(self.mark_dirty)
        self.draft_recovery = QWidget()
        recovery = QHBoxLayout(self.draft_recovery)
        recovery.setContentsMargins(0, 0, 0, 0)
        self.draft_recovery_text = hint("")
        recovery.addWidget(self.draft_recovery_text)
        self.recover_button = button("Khôi phục", lambda: self.guard(self.recover_draft))
        recovery.addWidget(self.recover_button)
        drafts_menu = menu_button("Khác")
        drafts_menu.menu().addAction("Bỏ các bản nháp cũ", self.discard_recovery_drafts)
        recovery.addWidget(drafts_menu)
        main.addWidget(self.draft_recovery)
        main.addWidget(QLabel("Tên bài"))
        main.addWidget(self.title)
        self.content = SummernoteEditor()
        self.content.notice = lambda message: self.statusBar().showMessage(message, 15000)
        self.content.setPlaceholderText("Vị trí tuyển dụng, mức lương, yêu cầu, quyền lợi, cách ứng tuyển…")
        self.content.textChanged.connect(self.mark_dirty)
        main.addWidget(self.content, 1)
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("Hashtag cuối bài · #tuyendung #ketoan")
        self.tags.textChanged.connect(self.mark_dirty)
        main.addWidget(self.tags)
        self.content.setToolTip("Ctrl+V để dán giữ định dạng; Ctrl+Shift+V để dán chữ thuần.")
        self.images = QListWidget()
        self.images.setViewMode(QListWidget.ViewMode.IconMode)
        self.images.setFlow(QListWidget.Flow.LeftToRight)
        self.images.setWrapping(False)
        self.images.setFixedHeight(94)
        self.images.setIconSize(QSize(48, 48))
        self.images.setGridSize(QSize(82, 76))
        self.images.itemSelectionChanged.connect(self.update_image_actions)
        self.images.model().rowsInserted.connect(self.update_image_actions)
        self.images.model().rowsRemoved.connect(self.update_image_actions)
        self.image_count = QLabel("Ảnh đính kèm · 0")
        self.image_menu = menu_button("Thao tác ảnh")
        self.image_open_action = self.image_menu.menu().addAction("Mở ảnh", self.open_image)
        self.image_up_action = self.image_menu.menu().addAction("Đưa lên trước", lambda: self.move_image(-1))
        self.image_down_action = self.image_menu.menu().addAction("Đưa ra sau", lambda: self.move_image(1))
        self.image_remove_action = self.image_menu.menu().addAction("Bỏ ảnh đã chọn", self.remove_image)
        image_actions = row(self.image_count)
        image_actions.addStretch()
        image_actions.addWidget(button("Thêm ảnh", self.add_images))
        image_actions.addWidget(self.image_menu)
        main.addLayout(image_actions)
        main.addWidget(self.images)
        self.autosave_note = hint("Chưa lưu bài")
        main.addWidget(self.autosave_note)
        self.save_button = button("Lưu bài", lambda: self.guard(self.save_post))
        self.editor_post_button = button("Chọn nhóm đăng", lambda: self.guard(self.post_this_article))
        self.preview_button = button("Xem trước", self.preview_article)
        editor_actions = row(self.preview_button)
        editor_actions.addStretch()
        editor_actions.addWidget(self.save_button)
        editor_actions.addWidget(self.editor_post_button)
        editor_scroll = QScrollArea()
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setWidget(editor_body)
        editor_outer.addWidget(editor_scroll, 1)
        editor_outer.addLayout(editor_actions)
        self.content.ready.connect(self.update_editor_actions)
        self.update_image_actions()
        self.update_editor_actions()
        split.addWidget(editor)
        split.setSizes([250, 850])
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        layout.addWidget(split)
        return page

    def update_editor_actions(self):
        if not hasattr(self, "editor_post_button"):
            return
        content = self.content.has_content()
        valid = bool(self.title.text().strip()) and content
        unsaved = self.dirty or self.post_id is None
        self.save_button.setEnabled(valid and unsaved)
        blocked = self.busy or getattr(self, "queue_active", False) or getattr(self, "monitor_running", False)
        self.editor_post_button.setEnabled(valid and not blocked)
        self.preview_button.setEnabled(content)
        self.duplicate_action.setEnabled(content)
        self.copy_article_action.setEnabled(content)
        self.delete_article_action.setEnabled(self.post_id is not None)
        self.save_button.setText("Lưu thay đổi" if self.dirty and self.post_id is not None else "Lưu bài")
        empty = not content and not self.title.text().strip()
        recovery = hasattr(self, "draft_timer") and bool(self.stored_drafts()) and empty
        primary(self.recover_button, recovery)
        primary(self.template_button, empty and not recovery)
        primary(self.save_button, not empty and unsaved)
        primary(self.editor_post_button, valid and not unsaved and not blocked)
        if not self.dirty:
            self.autosave_note.setText("Đã lưu bài" if self.post_id is not None else "")
        self.save_button.setToolTip("" if valid else "Nhập tên và nội dung bài trước")
        self.editor_post_button.setToolTip(
            "Lưu bài và chọn nhóm đăng" if unsaved else "Chọn nhóm để đăng bài này"
        )

    def update_image_actions(self, *args):
        if not hasattr(self, "image_menu"):
            return
        count = self.images.count()
        index = self.images.currentRow()
        self.image_count.setText(f"Ảnh đính kèm · {count}")
        self.images.setVisible(count > 0)
        self.image_menu.setEnabled(index >= 0)
        self.image_open_action.setEnabled(index >= 0)
        self.image_remove_action.setEnabled(index >= 0)
        self.image_up_action.setEnabled(index > 0)
        self.image_down_action.setEnabled(0 <= index < count - 1)

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
        self.statusBar().showMessage("Đã tạo bài từ mẫu", 15000)

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
        dialog.resize(680, min(760, max(520, self.height() - 100)))
        layout = QVBoxLayout(dialog)
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
        actions.button(QDialogButtonBox.StandardButton.Close).setText("Đóng")
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
            if post["id"] == self.post_id:
                self.post_list.setCurrentItem(item)
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
        self.post_list.setCurrentItem(item)
        self.title.setText(post["title"])
        self.content.setHtml(post["html"])
        self.tags.setText(post["tags"])
        self.images.clear()
        for image in post["images"]:
            self.add_image_item(image)
        self.loading = False
        self.dirty = False
        self.save_button.setText("Lưu bài")
        self.update_editor_actions()

    def new_post(self):
        if not self.confirm_discard():
            return
        self.loading = True
        self.post_id = None
        self.post_list.setCurrentRow(-1)
        self.title.clear()
        self.content.clear()
        self.tags.clear()
        self.images.clear()
        self.loading = False
        self.dirty = False
        self.save_button.setText("Lưu bài")
        self.update_editor_actions()
        self.title.setFocus()

    def duplicate_post(self):
        self.post_id = None
        self.post_list.setCurrentRow(-1)
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
        self.update_editor_actions()
        self.refresh_posts()
        self.statusBar().showMessage("Đã lưu bài viết", 5000)
        return self.post_id

    def delete_post(self):
        if self.post_id is None:
            return
        if (
            QMessageBox.question(
                self, "Xóa bài", "Xóa bài đang mở khỏi thư viện? Các lượt đã tạo vẫn được giữ."
            )
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
        self.statusBar().showMessage("Đã sao chép bài", 10000)

    def build_positions(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        sidebar = QWidget()
        sidebar.setObjectName("panel")
        side = QVBoxLayout(sidebar)
        self.position_count = QLabel("Vị trí tuyển dụng")
        self.position_count.setObjectName("sectionTitle")
        side.addWidget(self.position_count)
        self.position_search = QLineEdit()
        self.position_search.setPlaceholderText("Tìm vị trí…")
        self.position_search.textChanged.connect(self.filter_positions)
        side.addWidget(self.position_search)
        self.position_list = QListWidget()
        self.position_list.itemClicked.connect(self.load_position)
        side.addWidget(self.position_list, 1)
        menu = menu_button("Thao tác")
        self.delete_position_action = menu.menu().addAction(
            "Xóa vị trí đang chọn", lambda: self.guard(self.delete_position)
        )
        side.addLayout(row(button("Vị trí mới", self.new_position), menu))
        layout.addWidget(sidebar, 1)
        panel = QWidget()
        panel.setObjectName("panel")
        form = QVBoxLayout(panel)
        form.addWidget(QLabel("Tên vị trí tuyển dụng *"))
        self.position_name = QLineEdit()
        self.position_name.setPlaceholderText("Ví dụ: Kỹ sư PLC, Kế toán, Kinh doanh")
        form.addWidget(self.position_name)
        form.addWidget(QLabel("Ghi chú"))
        self.position_notes = QTextEdit()
        self.position_notes.setAcceptRichText(False)
        form.addWidget(self.position_notes, 1)
        self.position_usage = hint("")
        form.addWidget(self.position_usage)
        self.position_save_button = button("Lưu vị trí", lambda: self.guard(self.save_position), True)
        actions = row()
        actions.addStretch()
        actions.addWidget(self.position_save_button)
        form.addLayout(actions)
        layout.addWidget(panel, 2)
        self.position_name.textChanged.connect(self.update_position_actions)
        self.position_notes.textChanged.connect(self.update_position_actions)
        self.update_position_actions()
        return page

    def position_values(self):
        return self.position_name.text(), self.position_notes.toPlainText()

    def update_position_actions(self):
        if not hasattr(self, "position_save_button"):
            return
        values = self.position_values()
        self.position_save_button.setEnabled(bool(values[0].strip()) and values != self.position_original)
        current = next((p for p in self.store.positions() if p["id"] == self.position_id), None)
        count = current["group_count"] if current else 0
        self.position_usage.setText(f"Đang gắn với {count} nhóm" if current else "")
        self.delete_position_action.setEnabled(bool(current) and count == 0)
        self.delete_position_action.setToolTip("Gỡ vị trí khỏi các nhóm trước khi xóa" if count else "")

    def confirm_position_switch(self):
        return (
            self.position_values() == self.position_original
            or QMessageBox.question(
                self,
                "Vị trí chưa lưu",
                "Bỏ thay đổi chưa lưu của vị trí này?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def new_position(self):
        if not self.confirm_position_switch():
            return
        self.position_id = None
        self.position_name.clear()
        self.position_notes.clear()
        self.position_original = self.position_values()
        self.position_list.setCurrentRow(-1)
        self.update_position_actions()
        self.position_name.setFocus()

    def load_position(self, item):
        if not self.confirm_position_switch():
            return
        value = next(
            (p for p in self.store.positions() if p["id"] == item.data(Qt.ItemDataRole.UserRole)), None
        )
        if not value:
            return
        self.position_id = value["id"]
        self.position_name.setText(value["name"])
        self.position_notes.setPlainText(value["notes"])
        self.position_original = self.position_values()
        self.update_position_actions()

    def refresh_positions(self):
        self.position_list.clear()
        positions = self.store.positions()
        for value in positions:
            item = QListWidgetItem(value["name"])
            item.setData(Qt.ItemDataRole.UserRole, value["id"])
            self.position_list.addItem(item)
            if value["id"] == self.position_id:
                self.position_list.setCurrentItem(item)
        self.position_count.setText(f"Vị trí · {len(positions)}")
        self.filter_positions()
        self.group_positions.set_items([(p["id"], p["name"]) for p in positions])
        self.refresh_audience_tags()
        self.update_position_actions()

    def filter_positions(self, *args):
        query = self.position_search.text().strip().casefold()
        for i in range(self.position_list.count()):
            item = self.position_list.item(i)
            item.setHidden(query not in item.text().casefold())

    def save_position(self):
        self.position_id = self.store.save_position(self.position_id, *self.position_values())
        self.position_original = self.position_values()
        self.refresh_positions()
        self.refresh_groups()
        self.statusBar().showMessage("Đã lưu vị trí", 5000)

    def add_position_inline(self):
        name, accepted = QInputDialog.getText(self, "Thêm vị trí", "Tên vị trí tuyển dụng")
        if accepted:
            selected = self.group_positions.checked_data()
            value = self.store.save_position(None, name)
            self.refresh_positions()
            self.group_positions.set_checked([*selected, value])

    def delete_position(self):
        if (
            self.position_id is not None
            and QMessageBox.question(
                self,
                "Xóa vị trí",
                "Xóa vị trí này?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.store.delete_position(self.position_id)
            self.position_id = None
            self.position_name.clear()
            self.position_notes.clear()
            self.position_original = self.position_values()
            self.refresh_positions()
            self.refresh_groups()

    def build_groups(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        split = QSplitter()
        sidebar = QWidget()
        sidebar.setObjectName("panel")
        sidebar.setMinimumWidth(210)
        sidebar.setMaximumWidth(330)
        side = QVBoxLayout(sidebar)
        self.group_count = QLabel("Nhóm · 0")
        self.group_count.setObjectName("sectionTitle")
        side.addWidget(self.group_count)
        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("Tìm tên, vị trí hoặc nhãn…")
        self.group_search.textChanged.connect(self.filter_group_list)
        side.addWidget(self.group_search)
        self.group_list = QListWidget()
        self.group_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.group_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.group_list.itemClicked.connect(self.load_group)
        side.addWidget(self.group_list, 1)
        group_menu = menu_button("Thao tác")
        self.delete_group_action = group_menu.menu().addAction("Xóa nhóm đang chọn", self.delete_group)
        side.addLayout(row(button("Nhóm mới", self.new_group), group_menu))
        split.addWidget(sidebar)
        form_widget = QWidget()
        form_widget.setObjectName("panel")
        group_outer = QVBoxLayout(form_widget)
        group_body = QWidget()
        group_body.setObjectName("editorBody")
        form = QVBoxLayout(group_body)
        form.setContentsMargins(0, 0, 0, 0)
        heading = QLabel("Thông tin nhóm")
        heading.setObjectName("sectionTitle")
        form.addWidget(heading)
        self.group_name = QLineEdit()
        self.group_name.setPlaceholderText("Tên nhóm trên Facebook")
        self.group_url = QLineEdit()
        self.group_url.setPlaceholderText("https://www.facebook.com/groups/…/")
        self.group_positions = CheckPicker("Chọn ít nhất một vị trí")
        self.group_positions.changed.connect(self.update_group_actions)
        self.category = TagPicker()
        self.category.changed.connect(self.update_group_actions)
        self.group_notes = QTextEdit()
        self.group_notes.setAcceptRichText(False)
        self.group_notes.setPlaceholderText("Quy định nhóm hoặc thông tin cần lưu ý…")
        for title, field in (("Tên nhóm *", self.group_name), ("Link Facebook *", self.group_url)):
            form.addWidget(QLabel(title))
            form.addWidget(field)
        form.addWidget(QLabel("Vị trí tuyển dụng *"))
        form.addLayout(
            row(self.group_positions, button("+ Vị trí", lambda: self.guard(self.add_position_inline)))
        )
        form.addWidget(QLabel("Nhãn phân loại"))
        form.addWidget(self.category)
        self.group_validation = hint("")
        self.group_validation.setStyleSheet("color:#b91c1c;")
        form.addWidget(self.group_validation)
        form.addWidget(QLabel("Ghi chú"))
        form.addWidget(self.group_notes, 1)
        self.group_open_button = button("Mở nhóm", self.open_group_editor)
        self.group_save_button = button("Lưu nhóm", lambda: self.guard(self.save_group), True)
        actions = row(self.group_open_button)
        actions.addStretch()
        actions.addWidget(self.group_save_button)
        group_scroll = QScrollArea()
        group_scroll.setWidgetResizable(True)
        group_scroll.setWidget(group_body)
        group_outer.addWidget(group_scroll, 1)
        group_outer.addLayout(actions)
        split.addWidget(form_widget)
        split.setSizes([250, 850])
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        layout.addWidget(split)
        for field in (self.group_name, self.group_url, self.group_notes):
            field.textChanged.connect(self.update_group_actions)
        self.update_group_actions()
        return page

    def update_group_actions(self):
        if not hasattr(self, "group_save_button"):
            return
        values = self.group_values()
        valid_url = False
        if self.group_url.text().strip():
            try:
                normalize_group(self.group_url.text())
                valid_url = True
            except ValueError:
                pass
        invalid = bool(self.group_url.text().strip()) and not valid_url
        missing_position = bool(values[0].strip()) and valid_url and not self.group_positions.checked_data()
        self.group_validation.setText(
            "Nhập link nhóm Facebook hợp lệ"
            if invalid
            else "Chọn ít nhất một vị trí tuyển dụng"
            if missing_position
            else ""
        )
        self.group_validation.setVisible(invalid or missing_position)
        self.group_save_button.setEnabled(
            bool(values[0].strip())
            and valid_url
            and bool(self.group_positions.checked_data())
            and values != getattr(self, "group_original", ("", "", "", "", ()))
        )
        self.group_open_button.setEnabled(valid_url)
        self.delete_group_action.setEnabled(self.group_id is not None)

    def open_group_editor(self):
        QDesktopServices.openUrl(QUrl(normalize_group(self.group_url.text())))

    def refresh_groups(self):
        current = self.job_groups.currentData()
        self.group_list.clear()
        self.job_groups.clear()
        for group in self.store.groups():
            item = QListWidgetItem(group["name"] + (f" · {group['category']}" if group["category"] else ""))
            item.setData(Qt.ItemDataRole.UserRole, group)
            item.setToolTip(
                item.text() + "\nVị trí: " + (", ".join(group["position_names"]) or "Chưa gán vị trí")
            )
            self.group_list.addItem(item)
            if group["id"] == self.group_id:
                self.group_list.setCurrentItem(item)
            self.job_groups.addItem(group["name"], group["id"])
        index = self.job_groups.findData(current)
        if index >= 0:
            self.job_groups.setCurrentIndex(index)
        self.refresh_audience_tags()
        self.filter_group_list()
        missing = sum(not g["position_ids"] for g in self.store.groups())
        self.group_count.setText(
            f"Nhóm · {self.group_list.count()}" + (f" · {missing} chưa gán" if missing else "")
        )
        labels = {t.casefold(): t for t in self.store.group_tags()}
        labels.update({t.casefold(): t for t in self.category.labels()})
        self.category.set_items(sorted(labels.items()))
        self.update_group_actions()

    def filter_group_list(self):
        query = self.group_search.text().casefold()
        for index in range(self.group_list.count()):
            item = self.group_list.item(index)
            item.setHidden(query not in (item.text() + " " + item.toolTip()).casefold())

    def load_group(self, item):
        if not self.confirm_group_switch():
            return
        group = item.data(Qt.ItemDataRole.UserRole)
        self.group_id = group["id"]
        self.group_list.setCurrentItem(item)
        self.group_name.setText(group["name"])
        self.group_url.setText(group["url"])
        self.group_positions.set_checked(group["position_ids"])
        self.category.setText(group["category"])
        self.group_notes.setPlainText(group["notes"])
        self.group_original = self.group_values()
        self.update_group_actions()

    def group_values(self):
        return (
            self.group_name.text(),
            self.group_url.text(),
            self.category.currentText(),
            self.group_notes.toPlainText(),
            tuple(sorted(self.group_positions.checked_data())),
        )

    def confirm_group_switch(self):
        values = self.group_values()
        original = getattr(self, "group_original", ("", "", "", "", ()))
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
        self.group_list.setCurrentRow(-1)
        for field in (self.group_name, self.group_url, self.category, self.group_notes, self.group_positions):
            field.clear()
        self.group_original = self.group_values()
        self.update_group_actions()

    def save_group(self):
        self.group_id = self.store.save_group(self.group_id, *self.group_values())
        self.group_original = self.group_values()
        self.update_group_actions()
        self.refresh_groups()
        self.statusBar().showMessage("Đã lưu nhóm", 5000)

    def delete_group(self):
        if (
            self.group_id is not None
            and QMessageBox.question(
                self, "Xóa nhóm", "Xóa nhóm này khỏi danh sách? Các lượt đã tạo vẫn được giữ."
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.store.delete_group(self.group_id)
            self.group_original = self.group_values()
            self.update_group_actions()
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
            self.diagnostic_export_button.setEnabled((self.store.root / "link-diagnostics.json").exists())
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
        account = QGroupBox("Tài khoản Facebook")
        account_layout = QVBoxLayout(account)
        self.settings_login_button = self.browser_button("Đăng nhập Facebook", "login")
        primary(self.settings_login_button, True)
        account_layout.addLayout(toolbar(self.settings_login_button))
        layout.addWidget(account)
        data = QGroupBox("Dữ liệu trên máy")
        data_layout = QVBoxLayout(data)
        location = QLineEdit(str(self.store.root))
        location.setReadOnly(True)
        data_layout.addWidget(location)
        data_layout.addLayout(
            toolbar(
                button(
                    "Mở thư mục dữ liệu",
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.root))),
                ),
                button("Sao lưu dữ liệu", self.backup),
            )
        )
        layout.addWidget(data)
        support = QGroupBox("Hỗ trợ")
        support_layout = QVBoxLayout(support)
        self.diagnostic_export_button = button("Xuất chẩn đoán", self.export_diagnostics)
        self.diagnostic_export_button.setEnabled((self.store.root / "link-diagnostics.json").exists())
        support_layout.addLayout(
            toolbar(
                button("Hướng dẫn sử dụng", lambda: self.quick_start.show()),
                self.diagnostic_export_button,
            )
        )
        layout.addWidget(support)
        layout.addStretch()
        self.update_label = hint("")
        layout.addWidget(self.update_label)
        self.update_button = button("Kiểm tra cập nhật", lambda: self.updates.check(True))
        layout.addLayout(toolbar(QLabel(f"Facebook Helper {__version__}"), self.update_button))
        return page

    def setup_updates(self, background):
        self.pending_update = None
        self.seen_updates = set()
        self.updates = UpdateChecker(self.store, self)
        self.updates.status.connect(self.update_label.setText)
        self.updates.available.connect(self.update_available)
        self.update_notice_timer = QTimer(self)
        self.update_notice_timer.setInterval(15000)
        self.update_notice_timer.timeout.connect(self.offer_update)
        if background:
            self.updates.start()

    def update_available(self, release):
        if release["version"] in self.seen_updates and not release.get("manual"):
            return
        self.pending_update = release
        self.offer_update()

    def ask_update(self, release):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Có bản cập nhật")
        dialog.setText(f"Đã có Facebook Helper {release['version']}. Tải bộ cài để cập nhật?")
        download = dialog.addButton("Tải bộ cài", QMessageBox.ButtonRole.AcceptRole)
        dialog.addButton("Để sau", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        return dialog.clickedButton() is download

    def offer_update(self):
        if not self.pending_update or self.closing:
            return
        if self.busy or self.queue_active or self.monitor_running:
            self.update_notice_timer.start()
            return
        self.update_notice_timer.stop()
        release = self.pending_update
        self.pending_update = None
        self.seen_updates.add(release["version"])
        if self.ask_update(release):
            QDesktopServices.openUrl(QUrl(release["url"]))
            self.update_label.setText("Đang tải bộ cài trong trình duyệt. Đóng ứng dụng trước khi cài.")

    def export_diagnostics(self):
        source = self.store.root / "link-diagnostics.json"
        if not source.exists():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất chẩn đoán", "facebook-helper-chan-doan.json", "JSON (*.json)"
        )
        if path:

            def export():
                Path(path).write_bytes(source.read_bytes())
                self.statusBar().showMessage("Đã xuất chẩn đoán", 5000)

            self.guard(export)

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
        if not self.confirm_group_switch() or not self.confirm_position_switch():
            self.configure_tracking()
            event.ignore()
            return
        self.dirty = False
        self.group_original = self.group_values()
        self.update_group_actions()
        self.updates.stop()
        self.update_notice_timer.stop()
        if self.browser.isRunning():
            # Do not destroy a running QThread; shutdown is asynchronous even during navigation.
            self.closing = True
            self.setEnabled(False)
            self.statusBar().showMessage("Đang đóng trình duyệt, vui lòng chờ…")
            self.browser.submit("stop")
            event.ignore()
            return
        event.accept()
