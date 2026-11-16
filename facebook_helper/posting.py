"""Audience selection and sequential posting, with one browser operation at a time."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpinBox,
)

from .widgets import button, hint, row

SENT = {"submitted", "pending", "published", "rejected", "skipped"}
READY = {"draft", "prepared", "error"}


class PostingMixin:
    def build_audience(self, layout):
        self.queue_active = False
        self.queue_auto = False
        self.queue_dispatching = False
        self.queue_batch_id = None
        self.authorized_auto_batch = None
        self.queue_timer = QTimer(self)
        self.queue_timer.setSingleShot(True)
        self.queue_timer.timeout.connect(lambda: self.guard(self.queue_continue))
        layout.addLayout(
            row(
                hint("Chọn bài → Chọn nhóm hoặc nhãn → Tạo danh sách → Bắt đầu"),
                self.browser_button("Đăng nhập Facebook", "login"),
            )
        )
        self.job_posts = QComboBox()
        self.job_posts.setMinimumWidth(260)
        self.batch_name = QLineEdit()
        self.batch_name.setPlaceholderText("Tên danh sách (không bắt buộc), ví dụ: Tuyển kỹ sư tháng 11")
        layout.addLayout(row(QLabel("Bài tuyển dụng"), self.job_posts, self.batch_name))
        self.audience_mode = QComboBox()
        self.audience_mode.addItems(["Một nhóm", "Nhiều nhóm", "Theo nhãn nhóm"])
        self.job_groups = QComboBox()
        self.audience_tag = QComboBox()
        self.audience_tag.setMinimumWidth(170)
        self.audience_mode.currentIndexChanged.connect(self.refresh_audience)
        self.audience_tag.currentIndexChanged.connect(self.refresh_audience)
        layout.addLayout(row(QLabel("Đăng ở đâu?"), self.audience_mode, self.job_groups, self.audience_tag))
        self.audience_list = QListWidget()
        self.audience_list.setMaximumHeight(105)
        self.audience_list.itemChanged.connect(self.update_audience_count)
        layout.addWidget(self.audience_list)
        layout.addWidget(
            hint(
                "Các nhóm được thực hiện theo thứ tự hiển thị, từ trên xuống. Bạn có thể bỏ chọn nhóm không cần."
            )
        )
        self.select_all_groups = button("Chọn tất cả nhóm đang hiện", lambda: self.check_audience(True))
        self.clear_groups = button("Bỏ chọn", lambda: self.check_audience(False))
        self.audience_count = hint("")
        layout.addLayout(
            row(
                self.audience_count,
                self.select_all_groups,
                self.clear_groups,
                button("Tạo danh sách đăng", lambda: self.guard(self.create_posting_batch), True),
            )
        )
        self.batch_filter = QComboBox()
        self.batch_filter.addItem("Tất cả lượt đăng", None)
        self.batch_filter.currentIndexChanged.connect(self.batch_changed)
        self.auto_send = QCheckBox("Tự đăng bài (ứng dụng bấm Đăng)")
        self.auto_send.setChecked(True)
        self.auto_send.setToolTip(
            "Đang bật: ứng dụng sẽ bấm Đăng sau khi bạn xác nhận. Bỏ chọn nếu chỉ muốn điền bài và tự bấm Đăng."
        )
        self.group_delay = QSpinBox()
        self.group_delay.setRange(5, 300)
        self.group_delay.setValue(15)
        self.group_delay.setSuffix(" giây giữa các nhóm")
        self.group_delay.hide()
        layout.addLayout(
            row(QLabel("Danh sách đang làm"), self.batch_filter, self.auto_send, self.group_delay)
        )
        self.queue_progress = hint("Tạo danh sách đăng để theo dõi từng nhóm và tiếp tục khi cần.")
        layout.addWidget(self.queue_progress)
        begin = button("Bắt đầu / tiếp tục", lambda: self.guard(self.start_posting_queue), True)
        following = button("Đã gửi · sang nhóm sau", lambda: self.guard(self.complete_queue_job))
        skip = button("Bỏ qua nhóm này", lambda: self.guard(self.skip_queue_job))
        self.begin_posting_button = begin
        self.posting_mode_hint = hint("")
        self.auto_send.toggled.connect(self.update_posting_mode)
        self.update_posting_mode()
        layout.addWidget(self.posting_mode_hint)
        self.browser_buttons.extend([begin, following, skip])
        layout.addLayout(row(begin, button("Tạm dừng", self.pause_posting_queue), following, skip))
        layout.addLayout(
            row(
                self.browser_button("Điền bài (nếu cần)", "fill"),
                button("Đăng bản đang mở", lambda: self.guard(self.publish_open_draft)),
            )
        )
        self.refresh_audience()

    def publish_open_draft(self):
        if self.busy:
            raise ValueError("Chờ thao tác hiện tại hoàn tất trước nhé.")
        job = self.current_job()
        if (
            QMessageBox.question(
                self,
                "Gửi bản đang mở trong Facebook",
                f"Nhóm: {job['group_name']}\nỨng dụng sẽ bấm Đăng cho bản hiện đang mở; không dán lại chữ và không thêm lại ảnh.\nBạn đã kiểm tra nội dung và ảnh trong Facebook?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.pause_posting_queue(announce=False)
        self.run_browser("publish_current")

    def update_posting_mode(self, *args):
        automatic = self.auto_send.isChecked()
        self.begin_posting_button.setText("Bắt đầu tự đăng" if automatic else "Chỉ chuẩn bị bài")
        self.posting_mode_hint.setText(
            "TỰ ĐĂNG: mở nhóm → dán bài → tải ảnh → bấm Đăng. Sau đó kiểm tra kết quả để sang nhóm tiếp."
            if automatic
            else "CHỈ CHUẨN BỊ: ứng dụng điền bài; bạn tự bấm Đăng trên Facebook."
        )

    def refresh_audience(self, *args):
        if not hasattr(self, "audience_list"):
            return
        old = {
            self.audience_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.audience_list.count())
            if self.audience_list.item(i).checkState() == Qt.CheckState.Checked
        }
        mode = self.audience_mode.currentIndex()
        self.job_groups.setVisible(mode == 0)
        self.audience_tag.setVisible(mode == 2)
        self.audience_list.setVisible(mode != 0)
        self.select_all_groups.setVisible(mode != 0)
        self.clear_groups.setVisible(mode != 0)
        groups = (
            self.store.groups_by_tag(self.audience_tag.currentText()) if mode == 2 else self.store.groups()
        )
        self.audience_list.blockSignals(True)
        self.audience_list.clear()
        for group in groups:
            item = QListWidgetItem(group["name"] + (f" · {group['category']}" if group["category"] else ""))
            item.setData(Qt.ItemDataRole.UserRole, group["id"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if mode == 2 or group["id"] in old else Qt.CheckState.Unchecked
            )
            self.audience_list.addItem(item)
        self.audience_list.blockSignals(False)
        self.update_audience_count()

    def refresh_audience_tags(self):
        previous = self.audience_tag.currentText()
        self.audience_tag.blockSignals(True)
        self.audience_tag.clear()
        self.audience_tag.addItems(self.store.group_tags())
        index = self.audience_tag.findText(previous)
        if index >= 0:
            self.audience_tag.setCurrentIndex(index)
        self.audience_tag.blockSignals(False)
        self.refresh_audience()

    def selected_group_ids(self):
        if self.audience_mode.currentIndex() == 0:
            value = self.job_groups.currentData()
            return [value] if value is not None else []
        return [
            self.audience_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.audience_list.count())
            if self.audience_list.item(i).checkState() == Qt.CheckState.Checked
        ]

    def check_audience(self, checked):
        for index in range(self.audience_list.count()):
            self.audience_list.item(index).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )

    def update_audience_count(self, *args):
        if self.audience_mode.currentIndex() == 2 and not self.audience_tag.currentText():
            self.audience_count.setText("Chưa có nhãn. Vào Nhóm & nhãn để thêm nhãn cho các nhóm trước nhé.")
            return
        self.audience_count.setText(
            f"Đã chọn {len(self.selected_group_ids())} nhóm · mỗi nhóm có kết quả riêng"
        )

    def create_posting_batch(self):
        if self.queue_active:
            raise ValueError("Tạm dừng danh sách đang chạy trước khi tạo danh sách mới nhé.")
        post_id, group_ids = self.job_posts.currentData(), self.selected_group_ids()
        if post_id is None or not group_ids:
            raise ValueError("Chọn một bài đã lưu và ít nhất một nhóm trước nhé.")
        if self.dirty and self.post_id == post_id:
            raise ValueError("Bài đang có thay đổi chưa lưu. Hãy lưu bài trước nhé.")
        duplicates = {
            job["group_name"]
            for job in self.store.jobs()
            if job["post_id"] == post_id and job["group_id"] in group_ids
        }
        if (
            duplicates
            and QMessageBox.question(
                self,
                "Bài đã có lịch sử ở một số nhóm",
                "Bài này đã có lượt đăng ở: " + ", ".join(sorted(duplicates)) + ".\nVẫn tạo danh sách mới?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        audience = (
            self.audience_tag.currentText() if self.audience_mode.currentIndex() == 2 else "Tự chọn nhóm"
        )
        batch_id = self.store.create_batch(post_id, group_ids, self.batch_name.text(), audience)
        self.refresh_batches(batch_id)
        first = self.store.batch_jobs(batch_id)[0]
        self.refresh_jobs(first["id"])
        self.statusBar().showMessage(
            f"Đã tạo danh sách {len(group_ids)} nhóm. Bấm Bắt đầu khi sẵn sàng.", 15000
        )
        return batch_id

    def refresh_batches(self, selected=None):
        selected = self.batch_filter.currentData() if selected is None else selected
        self.batch_filter.blockSignals(True)
        self.batch_filter.clear()
        self.batch_filter.addItem("Tất cả lượt đăng", None)
        for batch in self.store.batches():
            self.batch_filter.addItem(
                f"#{batch['id']} · {batch['title']} · {batch['total']} nhóm", batch["id"]
            )
        index = self.batch_filter.findData(selected)
        self.batch_filter.setCurrentIndex(max(index, 0))
        self.batch_filter.blockSignals(False)
        self.update_queue_progress()

    def batch_changed(self, *args):
        self.pause_posting_queue(announce=False)
        self.refresh_jobs()
        self.update_queue_progress()

    def update_queue_progress(self):
        batch_id = self.batch_filter.currentData()
        jobs = self.store.batch_jobs(batch_id) if batch_id is not None else []
        if not jobs:
            self.queue_progress.setText(
                "Chọn một danh sách để bắt đầu. Bạn có thể lưu nhiều danh sách cho nhiều bài khác nhau."
            )
            return
        done = sum(job["status"] in {"pending", "published", "rejected", "skipped"} for job in jobs)
        errors = sum(job["status"] in {"error", "uncertain", "sending", "submitted"} for job in jobs)
        suffix = (
            " · Đang thực hiện"
            if self.queue_active
            else " · Đang tạm dừng"
            if done < len(jobs)
            else " · Đã xử lý hết"
        )
        self.queue_progress.setText(
            f"Tiến độ: {done}/{len(jobs)} nhóm đã xử lý · {errors} nhóm cần kiểm tra" + suffix
        )

    def next_queue_job(self, batch_id):
        for job in self.store.batch_jobs(batch_id):
            if job["status"] in {"uncertain", "sending", "submitted"}:
                if job["status"] == "sending":
                    self.store.update_job(job["id"], status="uncertain")
                self.refresh_jobs(job["id"])
                raise ValueError(
                    f"Cần kiểm tra bài trong nhóm {job['group_name']} trước khi tiếp tục để tránh gửi trùng. "
                    "Hãy cập nhật kết quả, hoặc chọn Bỏ qua nhóm này."
                )
            if job["status"] in READY:
                return job
        return None

    def start_posting_queue(self):
        if self.busy or self.queue_active:
            raise ValueError("Danh sách đang được thực hiện. Bấm Tạm dừng trước khi bắt đầu lại.")
        batch_id = self.batch_filter.currentData()
        if batch_id is None:
            raise ValueError("Chọn một danh sách đăng trước nhé.")
        job = self.next_queue_job(batch_id)
        if job is None:
            self.update_queue_progress()
            self.statusBar().showMessage("Danh sách này đã được xử lý hết.", 10000)
            return
        automatic = self.auto_send.isChecked()
        if automatic:
            jobs = [entry for entry in self.store.batch_jobs(batch_id) if entry["status"] in READY]
            names = "\n".join(f"• {entry['group_name']}" for entry in jobs)
            if (
                QMessageBox.question(
                    self,
                    "Xác nhận tự gửi bài",
                    f"Bài: {job['title']}\nNhóm sắp đăng: {job['group_name']}\nDanh sách có {len(jobs)} nhóm còn lại:\n"
                    + names
                    + "\n\nSau mỗi bài, xác nhận kết quả rồi tiếp tục nhóm sau. Bạn đã kiểm tra bài, ảnh và các nhóm này?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
            self.authorized_auto_batch = batch_id
        self.queue_auto = automatic
        self.queue_batch_id = batch_id
        self.queue_active = True
        self.dispatch_queue_job(job)

    def dispatch_queue_job(self, job):
        self.refresh_batches(job["batch_id"])
        self.history_search.clear()
        self.refresh_jobs(job["id"])
        self.queue_dispatching = True
        try:
            self.run_browser("publish" if self.queue_auto else "prepare")
        except Exception:
            self.pause_posting_queue(announce=False)
            raise
        finally:
            self.queue_dispatching = False
        self.update_queue_progress()

    def queue_continue(self):
        if not self.queue_active:
            return
        try:
            job = self.next_queue_job(self.queue_batch_id)
        except Exception:
            self.pause_posting_queue(announce=False)
            raise
        if job is None:
            self.pause_posting_queue(announce=False)
            self.update_queue_progress()
            self.statusBar().showMessage(
                "Đã xử lý hết danh sách. Hãy kiểm tra bài, lấy link và lưu minh chứng.", 20000
            )
            return
        self.dispatch_queue_job(job)

    def pause_posting_queue(self, announce=True):
        self.queue_active = False
        self.queue_timer.stop()
        if hasattr(self, "batch_filter"):
            self.update_queue_progress()
        if announce:
            self.statusBar().showMessage(
                "Đã tạm dừng. Thao tác đang chạy (nếu có) sẽ hoàn tất; không chuyển sang nhóm khác.", 15000
            )

    def queue_browser_done(self, action, result):
        if action not in {"prepare", "publish", "publish_current"}:
            return
        if (
            result.get("uncertain")
            or result.get("needs_composer")
            or (action in {"publish", "publish_current"} and not result.get("sent"))
        ):
            self.pause_posting_queue(announce=False)
            return
        if action in {"publish", "publish_current"} and result.get("sent"):
            self.pause_posting_queue(announce=False)
            self.statusBar().showMessage(
                "Đã bấm Đăng. Kiểm tra bài còn hiển thị/chờ duyệt; chọn kết quả thực tế trước khi tiếp tục. Không tự gửi tiếp.",
                30000,
            )
        self.update_queue_progress()

    def complete_queue_job(self):
        if self.busy:
            raise ValueError("Chờ thao tác hiện tại hoàn tất trước nhé.")
        if self.queue_active and self.queue_auto:
            raise ValueError("Đang tự gửi. Bấm Tạm dừng để cập nhật bằng tay.")
        job = self.current_job()
        if job["batch_id"] is None:
            raise ValueError("Lượt này chưa thuộc danh sách. Bạn có thể lưu kết quả bằng nút Lưu trạng thái.")
        if job["status"] not in SENT or job["status"] == "submitted":
            answer, ok = QInputDialog.getItem(
                self,
                "Bạn đã bấm Đăng trên Facebook?",
                "Kết quả của bài vừa gửi:",
                ["Đã gửi, cần kiểm tra lại", "Đã gửi, đang chờ duyệt", "Đã hiển thị (cần link bài)"],
                0,
                False,
            )
            if not ok:
                return
            status = {"Đã gửi, cần kiểm tra lại": "submitted", "Đã gửi, đang chờ duyệt": "pending"}.get(
                answer, "published"
            )
            if status == "submitted":
                self.store.update_job(
                    job["id"],
                    status="submitted",
                    note="Người dùng báo đã bấm Đăng; cần kiểm tra trước khi tiếp tục.",
                )
                self.pause_posting_queue(announce=False)
                self.refresh_jobs(job["id"])
                return
            url = self.link.text().strip()
            if status == "published" and not url:
                url, ok = QInputDialog.getText(self, "Link bài đã hiển thị", "Dán link của bài vừa đăng:")
                if not ok:
                    return
            self.store.update_job(job["id"], status=status, url=url, note=self.job_note.text())
        self.continue_after_result(job["batch_id"])

    def continue_after_result(self, batch_id):
        self.queue_batch_id = batch_id
        self.queue_auto = self.auto_send.isChecked()
        if self.queue_auto and self.authorized_auto_batch != batch_id:
            self.queue_active = False
            self.start_posting_queue()
            return
        self.queue_active = True
        self.queue_continue()

    def skip_queue_job(self):
        if self.busy:
            raise ValueError("Chờ thao tác hiện tại hoàn tất trước nhé.")
        job = self.current_job()
        if job["batch_id"] is None:
            raise ValueError("Chọn một lượt trong danh sách đăng trước nhé.")
        if (
            QMessageBox.question(
                self,
                "Bỏ qua nhóm",
                f"Bỏ qua nhóm {job['group_name']} trong danh sách này?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.pause_posting_queue(announce=False)
        self.store.update_job(job["id"], status="skipped")
        self.continue_after_result(job["batch_id"])
