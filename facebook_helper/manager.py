"""Posting register: filters, monitoring controls and auditable observations."""

from datetime import datetime

from PySide6.QtCore import QDate, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
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
        self.status.addItem("Cần xử lý", "attention")
        filters_toggle = button("Lọc thêm và cài đặt kiểm tra", lambda: None)
        filters_toggle.setCheckable(True)
        layout.addLayout(row(self.keyword, filters_toggle))
        layout.addLayout(
            row(
                *[
                    button(label, lambda checked=False, key=key: self.quick_filter(key))
                    for label, key in [
                        ("Tất cả", "all"),
                        ("Hôm nay", "today"),
                        ("7 ngày qua", "week"),
                        ("Chờ duyệt", "pending"),
                        ("Cần xử lý", "attention"),
                    ]
                ]
            )
        )
        self.filters_panel = QWidget()
        filters = QVBoxLayout(self.filters_panel)
        filters_toggle.toggled.connect(self.filters_panel.setVisible)
        layout.addWidget(self.filters_panel)
        filters.addLayout(row(self.post, self.group, self.tag, self.status))
        filters.addLayout(
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
        filters.addLayout(row(self.periodic, self.interval))
        self.filters_panel.hide()
        self.monitor_message = hint("Tích ô trước các bài cần kiểm tra, rồi bấm Kiểm tra bài đã chọn.")
        layout.addWidget(self.monitor_message)
        self.check_selected_button = button(
            "Kiểm tra bài đã chọn", lambda: self.check_requested.emit(self.selected_ids()), True
        )
        layout.addLayout(row(self.check_selected_button, button("Dừng kiểm tra", self.stop_requested.emit)))
        filters.addWidget(
            button(
                "Kiểm tra toàn bộ kết quả đang lọc",
                lambda: self.check_requested.emit([j["id"] for j in self.filtered_jobs]),
            )
        )
        self.select_all = QCheckBox("Chọn tất cả kết quả đang hiện")
        self.select_all.toggled.connect(self.set_all_checked)
        self.summary = hint("")
        layout.addLayout(row(self.select_all, self.summary))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Chọn", "Bài tuyển dụng", "Nhóm", "Kết quả", "Gửi lúc"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column in (0, 4):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.itemChanged.connect(self.update_selection_summary)
        self.table.itemSelectionChanged.connect(self.update_details)
        self.table.itemDoubleClicked.connect(lambda *_: self.details_panel.show())
        layout.addWidget(self.table)
        layout.addLayout(
            row(
                button("Mở bài Facebook", self.open_link),
                button("Sao chép link", self.copy_link),
                button(
                    "Xem chi tiết", lambda: self.details_panel.setVisible(not self.details_panel.isVisible())
                ),
                button("Xuất Excel đã chọn", lambda: self.export_filtered(selected_only=True)),
                button("Xuất Excel đang lọc", self.export_filtered),
            )
        )
        self.details_panel = QWidget()
        detail_layout = QVBoxLayout(self.details_panel)
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        detail_layout.addWidget(button("Xem lịch sử cập nhật", self.show_history))
        layout.addWidget(self.details_panel)
        self.details_panel.hide()
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
            self.select_all.blockSignals(True)
            self.select_all.setChecked(False)
            self.select_all.blockSignals(False)
            self.check_selected_button.setEnabled(False)
            self.update_details()
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
            status = self.status.currentData()
            if status == "attention":
                if job["status"] not in {"error", "uncertain", "sending"}:
                    continue
            elif status and job["status"] != status:
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
        current = self.current_job_record()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.filtered_jobs))
        self.table.clearSelection()
        for index, job in enumerate(self.filtered_jobs):
            check = QTableWidgetItem()
            check.setData(Qt.ItemDataRole.UserRole, job["id"])
            check.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
            )
            check.setCheckState(Qt.CheckState.Checked if job["id"] in selected else Qt.CheckState.Unchecked)
            self.table.setItem(index, 0, check)
            label = (
                "Đã gửi · chưa xác minh hiển thị" if job["status"] == "submitted" else STATUSES[job["status"]]
            )
            if job["check_outcome"] == "unknown" and job["status"] != "submitted":
                label += "\nChưa xác minh lại"
            for column, value in enumerate(
                (job["title"], job["group_name"], label, show_time(job["sent_at"])), start=1
            ):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value) + ("\n" + job["check_note"] if column == 3 else ""))
                if column == 3:
                    color = (
                        "#166534"
                        if job["status"] == "published"
                        else "#92400e"
                        if job["status"] == "pending"
                        else "#b91c1c"
                        if job["status"] in {"error", "uncertain", "rejected", "removed"}
                        else "#334155"
                    )
                    if job["check_outcome"] == "unknown":
                        color = "#92400e"
                    item.setForeground(QColor(color))
                self.table.setItem(index, column, item)
        self.table.blockSignals(False)
        row_index = next(
            (i for i, j in enumerate(self.filtered_jobs) if current and j["id"] == current["id"]), 0
        )
        if self.filtered_jobs:
            self.table.setCurrentCell(row_index, 1)
        self.table.resizeRowsToContents()
        self.update_selection_summary()
        self.update_details()

    def update_selection_summary(self, *args):
        ids = self.selected_ids()
        self.check_selected_button.setEnabled(bool(ids))
        self.select_all.blockSignals(True)
        self.select_all.setChecked(bool(self.filtered_jobs) and len(ids) == len(self.filtered_jobs))
        self.select_all.blockSignals(False)
        active = " · ".join(
            x.currentText()
            for x in (self.status, self.group, self.tag, self.post)
            if x.currentData() is not None
        )
        if self.use_dates.isChecked():
            active += f" · {self.date_field.currentText()}: {self.start.text()}–{self.end.text()}"
        self.summary.setText(
            f"{len(self.filtered_jobs)} kết quả · Đã chọn {len(ids)}" + (" · " + active if active else "")
        )

    def selected_ids(self):
        return [
            self.table.item(i, 0).data(Qt.ItemDataRole.UserRole)
            for i in range(self.table.rowCount())
            if self.table.item(i, 0) and self.table.item(i, 0).checkState() == Qt.CheckState.Checked
        ]

    def set_all_checked(self, checked):
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.table.blockSignals(False)
        self.update_selection_summary()

    def current_job_record(self):
        index = self.table.currentRow()
        item = self.table.item(index, 0) if index >= 0 else None
        return self.store.job(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def selected_link(self):
        job = self.current_job_record()
        return job["url"] if job else ""

    def update_details(self):
        if not hasattr(self, "detail_text"):
            return
        job = self.current_job_record()
        self.detail_text.setPlainText(
            f"{job['title']}\nNhóm: {job['group_name']}\nTrạng thái đã biết: {STATUSES[job['status']]}\n"
            f"Gửi: {show_time(job['sent_at'])} · Kiểm tra: {show_time(job['checked_at'])} · Lần đầu thấy hiển thị: {show_time(job['first_visible_at'])}\n"
            f"Link: {job['url'] or 'Chưa lấy được link'}\nKiểm tra: {job['check_note'] or 'Chưa kiểm tra'}\nGhi chú: {job['note']}"
            if job
            else "Bấm vào một bài để xem thông tin chi tiết."
        )

    def quick_filter(self, key):
        for field in (self.status, self.group, self.tag, self.post):
            field.blockSignals(True)
            field.setCurrentIndex(0)
            field.blockSignals(False)
        self.use_dates.blockSignals(True)
        self.use_dates.setChecked(key in {"today", "week"})
        self.use_dates.blockSignals(False)
        if key in {"today", "week"}:
            for field in (self.date_field, self.start, self.end):
                field.blockSignals(True)
            self.date_field.setCurrentIndex(self.date_field.findData("sent_at"))
            self.start.setDate(QDate.currentDate().addDays(-6 if key == "week" else 0))
            self.end.setDate(QDate.currentDate())
            for field in (self.date_field, self.start, self.end):
                field.blockSignals(False)
        elif key in {"pending", "attention"}:
            self.status.setCurrentIndex(self.status.findData(key))
        if key == "all":
            self.keyword.clear()
        self.refresh()

    def open_link(self):
        if self.selected_link():
            QDesktopServices.openUrl(QUrl(self.selected_link()))

    def copy_link(self):
        if self.selected_link():
            QApplication.clipboard().setText(self.selected_link())

    def show_history(self):
        current = self.current_job_record()
        ids = [current["id"]] if current else []
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
