"""Searchable posting register, independent of the active sending queue."""

from datetime import datetime

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .domain import STATUSES
from .widgets import button, hint, row


class PostManager(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Quản lý bài đăng"))
        layout.addWidget(
            hint(
                "Tìm theo ngày tạo lượt đăng, nội dung, nhóm, ghi chú hoặc link. Đã gửi và đã hiển thị là các trạng thái khác nhau."
            )
        )
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("Tìm từ khóa trong bài, nhóm, nội dung, link…")
        self.status = QComboBox()
        self.status.addItem("Tất cả trạng thái", None)
        for key, label in STATUSES.items():
            self.status.addItem(label, key)
        self.use_dates = QCheckBox("Lọc khoảng ngày")
        self.start = QDateEdit(QDate.currentDate().addDays(-30))
        self.end = QDateEdit(QDate.currentDate())
        for field in (self.start, self.end):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
        layout.addLayout(row(self.keyword, self.status))
        layout.addLayout(
            row(
                self.use_dates,
                QLabel("Từ ngày"),
                self.start,
                QLabel("Đến ngày"),
                self.end,
                button("Làm mới", self.refresh),
            )
        )
        self.summary = hint("")
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Mã", "Bài tuyển dụng", "Nhóm", "Trạng thái", "Ngày tạo", "Link bài", "Ghi chú"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        layout.addLayout(row(button("Mở bài Facebook", self.open_link), button("Copy link", self.copy_link)))
        for field in (self.keyword, self.status, self.use_dates, self.start, self.end):
            signal = (
                field.textChanged
                if field is self.keyword
                else field.currentIndexChanged
                if field is self.status
                else field.toggled
                if field is self.use_dates
                else field.dateChanged
            )
            signal.connect(self.refresh)
        self.refresh()

    def refresh(self, *args):
        if self.use_dates.isChecked() and self.start.date() > self.end.date():
            self.table.setRowCount(0)
            self.summary.setText("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")
            return
        query = self.keyword.text().strip().casefold()
        rows = []
        for job in self.store.jobs():
            created = datetime.fromisoformat(job["created_at"]).astimezone()
            date = QDate(created.year, created.month, created.day)
            if self.use_dates.isChecked() and not self.start.date() <= date <= self.end.date():
                continue
            if self.status.currentData() and job["status"] != self.status.currentData():
                continue
            if (
                query
                and query
                not in " ".join(
                    str(job[key]) for key in ("title", "group_name", "body", "note", "url")
                ).casefold()
            ):
                continue
            rows.append((job, created))
        self.table.setRowCount(len(rows))
        for index, (job, created) in enumerate(rows):
            for column, value in enumerate(
                (
                    job["id"],
                    job["title"],
                    job["group_name"],
                    STATUSES[job["status"]],
                    created.strftime("%d/%m/%Y %H:%M"),
                    job["url"],
                    job["note"],
                )
            ):
                self.table.setItem(index, column, QTableWidgetItem(str(value)))
        self.summary.setText(f"Tìm thấy {len(rows)} lượt đăng · ngày theo giờ trên máy của bạn")

    def selected_link(self):
        index = self.table.currentRow()
        return self.table.item(index, 5).text() if index >= 0 else ""

    def open_link(self):
        if self.selected_link():
            QDesktopServices.openUrl(QUrl(self.selected_link()))

    def copy_link(self):
        if self.selected_link():
            QApplication.clipboard().setText(self.selected_link())
