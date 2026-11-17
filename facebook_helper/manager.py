"""A compact posting register with explicit date, batch and keyword searches."""

from datetime import datetime

from PySide6.QtCore import QDate, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .widgets import button, row


def local_date(value):
    return datetime.fromisoformat(value).astimezone() if value else None


def show_time(value):
    parsed = local_date(value)
    return parsed.strftime("%d/%m/%Y %H:%M") if parsed else "—"


def send_label(job):
    if job["status"] in {"submitted", "pending", "published", "rejected", "removed"}:
        return "Đã gửi"
    return {
        "error": "Gửi lỗi",
        "uncertain": "Cần xem lại",
        "sending": "Đang gửi",
        "skipped": "Đã bỏ qua",
    }.get(job["status"], "Chưa gửi")


class PostManager(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.filtered_jobs = []
        self.criteria = None
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.batch = QComboBox()
        self.batch.setMinimumWidth(220)
        self.batch.setMinimumContentsLength(20)
        self.batch.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.start = QDateEdit(QDate.currentDate().addDays(-30))
        self.end = QDateEdit(QDate.currentDate())
        for field in (self.start, self.end):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
        filters = row(
            QLabel("Đợt đăng"), self.batch, QLabel("Từ ngày"), self.start, QLabel("Đến ngày"), self.end
        )
        filters.setStretch(1, 1)
        layout.addLayout(filters)
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("Tìm bài viết, nhóm hoặc link…")
        self.search_button = button("Tìm kiếm", self.search, True)
        search_row = row(self.keyword, self.search_button)
        search_row.setStretch(0, 1)
        layout.addLayout(search_row)
        self.keyword.returnPressed.connect(self.search)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Đợt đăng", "Bài viết", "Nhóm", "Thời gian", "Kết quả", "Link bài"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column in (3, 4):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.itemSelectionChanged.connect(self.update_actions)
        self.table.itemDoubleClicked.connect(lambda *_: self.open_link())
        layout.addWidget(self.table, 1)
        self.open_button = button("Mở bài", self.open_link)
        self.copy_button = button("Sao chép link", self.copy_link)
        self.export_button = button("Xuất Excel", self.export_filtered)
        self.summary = QLabel()
        actions = row(self.open_button, self.copy_button, self.export_button)
        actions.addStretch()
        actions.addWidget(self.summary)
        layout.addLayout(actions)
        self.search()

    def search(self):
        if self.start.date() > self.end.date():
            self.summary.setText("Từ ngày phải trước hoặc bằng Đến ngày.")
            return
        self.criteria = (
            self.batch.currentData(),
            self.start.date(),
            self.end.date(),
            self.keyword.text().strip().casefold(),
        )
        self.refresh()

    def refresh(self, *args):
        selected_job = self.current_job_record()
        selected_batch = self.batch.currentData()
        self.batch.clear()
        self.batch.addItem("Tất cả đợt đăng", None)
        for batch in self.store.batches():
            self.batch.addItem(
                f"#{batch['id']} · {batch['title']} · {show_time(batch['created_at'])}", batch["id"]
            )
        self.batch.setCurrentIndex(max(0, self.batch.findData(selected_batch)))
        batch_id, start, end, query = self.criteria
        self.filtered_jobs = []
        for job in self.store.posting_register():
            when = local_date(job["activity_at"])
            if not when or not start <= QDate(when.year, when.month, when.day) <= end:
                continue
            if batch_id is not None and job["batch_id"] != batch_id:
                continue
            searchable = " ".join(
                str(job[k] or "") for k in ("title", "body", "group_name", "url", "note", "batch_title")
            )
            if query and query not in searchable.casefold():
                continue
            self.filtered_jobs.append(job)
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(len(self.filtered_jobs))
        self.table.clearSelection()
        for index, job in enumerate(self.filtered_jobs):
            values = (
                f"#{job['batch_id']} · {job['batch_title']}" if job["batch_id"] else "—",
                job["title"],
                job["group_name"],
                show_time(job["activity_at"]),
                send_label(job),
                job["url"] or "Chưa có link",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, job["id"])
                item.setToolTip(value)
                if column == 4:
                    item.setForeground(
                        QColor(
                            "#166534"
                            if value == "Đã gửi"
                            else "#b91c1c"
                            if value in {"Gửi lỗi", "Cần xem lại"}
                            else "#334155"
                        )
                    )
                self.table.setItem(index, column, item)
        if self.filtered_jobs:
            index = next(
                (
                    i
                    for i, j in enumerate(self.filtered_jobs)
                    if selected_job and j["id"] == selected_job["id"]
                ),
                0,
            )
            self.table.setCurrentCell(index, 0)
        self.table.blockSignals(False)
        self.summary.setText(f"{len(self.filtered_jobs)} bài")
        self.update_actions()

    def current_job_record(self):
        index = self.table.currentRow()
        item = self.table.item(index, 0) if index >= 0 else None
        return self.store.job(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def selected_link(self):
        job = self.current_job_record()
        return job["url"] if job else ""

    def update_actions(self):
        available = bool(self.selected_link())
        self.open_button.setEnabled(available)
        self.copy_button.setEnabled(available)
        self.export_button.setEnabled(bool(self.filtered_jobs))

    def open_link(self):
        if self.selected_link():
            QDesktopServices.openUrl(QUrl(self.selected_link()))

    def copy_link(self):
        if self.selected_link():
            QApplication.clipboard().setText(self.selected_link())

    def export_filtered(self):
        if not self.filtered_jobs:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất kết quả tìm kiếm", "bai-dang.xlsx", "Excel (*.xlsx)"
        )
        if path:
            try:
                self.store.export_excel(path, self.filtered_jobs)
            except Exception as exc:
                QMessageBox.warning(self, "Chưa xuất được Excel", str(exc))
