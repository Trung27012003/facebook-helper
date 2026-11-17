"""Posting register: filters, monitoring controls and auditable observations."""

from datetime import datetime

from PySide6.QtCore import QDate, QItemSelectionModel, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .domain import STATUSES, parse_tags
from .widgets import button, hint, row


def local_date(value):
    return datetime.fromisoformat(value).astimezone() if value else None


def show_time(value):
    parsed = local_date(value)
    return parsed.strftime("%d/%m/%Y %H:%M") if parsed else "—"


class PostManager(QWidget):
    check_requested = Signal(list)
    stop_requested = Signal()
    settings_changed = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.filtered_jobs = []
        layout = QVBoxLayout(self)
        self.overview = hint("")
        layout.addWidget(self.overview)
        layout.addWidget(
            hint("Đã gửi khác với đã duyệt. Kiểm tra chỉ đọc Facebook; không gửi lại hay tự xóa bài.")
        )
        self.keyword = QLineEdit()
        self.keyword.setPlaceholderText("Tìm tiêu đề, nội dung, nhóm, ghi chú hoặc link…")
        self.status = QComboBox()
        self.status.addItem("Tất cả trạng thái", None)
        for key, label in STATUSES.items():
            self.status.addItem(label, key)
        self.group = QComboBox()
        self.tag = QComboBox()
        self.post = QComboBox()
        self.use_dates = QCheckBox("Lọc khoảng ngày")
        self.date_field = QComboBox()
        self.date_field.addItem("Ngày tạo lượt", "created_at")
        self.date_field.addItem("Ngày gửi thực tế", "sent_at")
        self.date_field.addItem("Ngày kiểm tra", "checked_at")
        self.start = QDateEdit(QDate.currentDate().addDays(-30))
        self.end = QDateEdit(QDate.currentDate())
        for field in (self.start, self.end):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
        layout.addLayout(row(self.keyword, self.status))
        layout.addLayout(row(self.post, self.group, self.tag))
        layout.addLayout(
            row(
                self.use_dates,
                self.date_field,
                QLabel("Từ"),
                self.start,
                QLabel("Đến"),
                self.end,
                button("Làm mới", self.refresh),
            )
        )
        self.periodic = QCheckBox("Tự kiểm tra khi ứng dụng mở và không đăng bài")
        self.periodic.setChecked(store.preference("monitor_enabled") == "1")
        self.interval = QSpinBox()
        self.interval.setRange(5, 1440)
        self.interval.setSuffix(" phút/lần")
        self.interval.setValue(int(store.preference("monitor_minutes", "30")))
        layout.addLayout(row(self.periodic, self.interval))
        self.monitor_message = hint(
            "Định kỳ kiểm tra bài đã gửi, chờ duyệt hoặc chưa rõ kết quả: tối đa 20 lượt/đợt, ưu tiên bài lâu chưa kiểm tra."
        )
        layout.addWidget(self.monitor_message)
        layout.addLayout(
            row(
                button("Kiểm tra bài đã chọn", lambda: self.check_requested.emit(self.selected_ids()), True),
                button(
                    "Kiểm tra các bài đang lọc",
                    lambda: self.check_requested.emit([j["id"] for j in self.filtered_jobs]),
                ),
                button("Dừng kiểm tra", self.stop_requested.emit),
            )
        )
        self.summary = hint("")
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "Mã",
                "Bài tuyển dụng",
                "Nhóm",
                "Trạng thái",
                "Gửi lúc",
                "Kiểm tra gần nhất",
                "Kết quả kiểm tra",
                "Link bài",
                "Ghi chú",
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate((45, 160, 180, 140, 135, 135, 155, 180, 260)):
            self.table.setColumnWidth(column, width)
        layout.addWidget(self.table)
        layout.addLayout(
            row(
                button("Mở bài Facebook", self.open_link),
                button("Copy link", self.copy_link),
                button("Lịch sử trạng thái", self.show_history),
                button("Xuất Excel đã chọn", lambda: self.export_filtered(selected_only=True)),
                button("Xuất Excel đang lọc", self.export_filtered),
            )
        )
        for field in (
            self.keyword,
            self.status,
            self.group,
            self.tag,
            self.post,
            self.date_field,
            self.use_dates,
            self.start,
            self.end,
        ):
            signal = (
                field.textChanged
                if field is self.keyword
                else field.currentIndexChanged
                if isinstance(field, QComboBox)
                else field.toggled
                if field is self.use_dates
                else field.dateChanged
            )
            signal.connect(self.refresh)
        self.periodic.toggled.connect(self.save_settings)
        self.interval.valueChanged.connect(self.save_settings)
        self.refresh()

    def save_settings(self, *args):
        self.store.set_preference("monitor_enabled", int(self.periodic.isChecked()))
        self.store.set_preference("monitor_minutes", self.interval.value())
        self.settings_changed.emit()

    def reload_filters(self, jobs):
        groups = {j["group_url"]: j["group_name"] for j in jobs}
        posts = {j["post_id"]: j["title"] for j in jobs if j["post_id"] is not None}
        for field, label, values in (
            (self.group, "Tất cả nhóm", groups),
            (self.post, "Tất cả bài", posts),
            (self.tag, "Tất cả nhãn nhóm", {t.casefold(): t for t in self.store.group_tags()}),
        ):
            selected = field.currentData()
            field.blockSignals(True)
            field.clear()
            field.addItem(label, None)
            for key, title in values.items():
                field.addItem(title, key)
            field.setCurrentIndex(max(0, field.findData(selected)))
            field.blockSignals(False)

    def refresh(self, *args):
        selected = self.selected_ids() if hasattr(self, "table") else []
        jobs = self.store.jobs()
        self.reload_filters(jobs)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        sent_today = sum(
            bool(j["sent_at"]) and local_date(j["sent_at"]).strftime("%Y-%m-%d") == today for j in jobs
        )
        remaining = sum(j["status"] in {"draft", "prepared"} for j in jobs)
        pending = sum(j["status"] == "pending" for j in jobs)
        attention = sum(j["status"] in {"error", "sending", "uncertain"} for j in jobs)
        self.overview.setText(
            f"Hôm nay gửi {sent_today} bài · Còn {remaining} lượt · Chờ duyệt {pending} · Cần xử lý {attention}"
        )
        self.filtered_jobs = []
        if self.use_dates.isChecked() and self.start.date() > self.end.date():
            self.table.setRowCount(0)
            self.summary.setText("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")
            return
        query = self.keyword.text().strip().casefold()
        tagged = {
            g["url"]
            for g in self.store.groups()
            if self.tag.currentData() in {t.casefold() for t in parse_tags(g["category"])}
        }
        for job in jobs:
            if self.use_dates.isChecked():
                value = local_date(job[self.date_field.currentData()])
                if (
                    value is None
                    or not self.start.date() <= QDate(value.year, value.month, value.day) <= self.end.date()
                ):
                    continue
            if self.status.currentData() and job["status"] != self.status.currentData():
                continue
            if self.group.currentData() and job["group_url"] != self.group.currentData():
                continue
            if self.post.currentData() is not None and job["post_id"] != self.post.currentData():
                continue
            if self.tag.currentData() and job["group_url"] not in tagged:
                continue
            if (
                query
                and query
                not in " ".join(
                    str(job[k]) for k in ("title", "group_name", "body", "note", "url", "check_note")
                ).casefold()
            ):
                continue
            self.filtered_jobs.append(job)
        self.table.setRowCount(len(self.filtered_jobs))
        self.table.clearSelection()
        for index, job in enumerate(self.filtered_jobs):
            outcome = (
                "Chưa xác minh được"
                if job["check_outcome"] == "unknown"
                else STATUSES.get(job["check_outcome"], "Chưa kiểm tra")
            )
            for column, value in enumerate(
                (
                    job["id"],
                    job["title"],
                    job["group_name"],
                    "Đã gửi" if job["status"] == "submitted" else STATUSES[job["status"]],
                    show_time(job["sent_at"]),
                    show_time(job["checked_at"]),
                    outcome,
                    job["url"],
                    job["note"],
                )
            ):
                item = QTableWidgetItem(str(value))
                item.setToolTip(
                    job["check_note"]
                    if column in {5, 6}
                    else STATUSES[job["status"]]
                    if column == 3
                    else str(value)
                )
                self.table.setItem(index, column, item)
            if job["id"] in selected:
                self.table.selectionModel().select(
                    self.table.model().index(index, 0),
                    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
                )
        self.summary.setText(
            f"Tìm thấy {len(self.filtered_jobs)} lượt · ngày theo giờ máy · giữ Ctrl/Shift để chọn nhiều bài"
        )

    def selected_ids(self):
        return [
            int(self.table.item(index.row(), 0).text())
            for index in self.table.selectionModel().selectedRows()
            if self.table.item(index.row(), 0)
        ]

    def selected_link(self):
        index = self.table.currentRow()
        return self.table.item(index, 7).text() if index >= 0 else ""

    def open_link(self):
        if self.selected_link():
            QDesktopServices.openUrl(QUrl(self.selected_link()))

    def copy_link(self):
        if self.selected_link():
            QApplication.clipboard().setText(self.selected_link())

    def show_history(self):
        ids = self.selected_ids()
        if len(ids) != 1:
            QMessageBox.information(self, "Lịch sử", "Chọn một bài để xem lịch sử trạng thái.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Lịch sử trạng thái và kiểm tra")
        dialog.resize(850, 500)
        layout = QVBoxLayout(dialog)
        view = QTextEdit()
        view.setReadOnly(True)
        events = self.store.events(ids[0])
        sources = {
            "manual": "Bạn cập nhật",
            "manual_sent": "Bạn xác nhận vừa gửi",
            "browser": "Kết quả gửi bài",
            "check": "Kiểm tra Facebook",
            "recovery": "Khôi phục sau gián đoạn",
        }
        view.setPlainText(
            "\n\n".join(
                f"{show_time(e['happened_at'])} · {sources.get(e['source'], e['source'])}\n{STATUSES[e['old_status']]} → {STATUSES[e['new_status']]}\n{e['note']}\n{e['url']}"
                for e in events
            )
            or "Chưa có sự kiện. Bản cũ chưa lưu lịch sử trạng thái."
        )
        layout.addWidget(view)
        dialog.exec()

    def export_filtered(self, selected_only=False):
        ids = set(self.selected_ids())
        jobs = [j for j in self.filtered_jobs if j["id"] in ids] if selected_only else self.filtered_jobs
        if not jobs:
            QMessageBox.information(self, "Xuất Excel", "Chọn bài hoặc điều chỉnh bộ lọc để có kết quả xuất.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất kết quả đang lọc", "bai-dang.xlsx", "Excel (*.xlsx)"
        )
        if path:
            try:
                self.store.export_excel(path, jobs)
            except Exception as exc:
                QMessageBox.warning(self, "Chưa xuất được Excel", str(exc))
