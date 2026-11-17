"""Audience selection and sequential posting, with one browser operation at a time."""

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .widgets import button, hint, row

SENT = {"submitted", "pending", "published", "rejected", "removed", "skipped"}
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
        choose, audience, review, run = self.init_posting_steps(layout)
        choose.addLayout(
            row(
                hint("Chọn bài bạn đã lưu, rồi bấm Tiếp tục."),
                self.browser_button("Đăng nhập Facebook", "login"),
                button("Mở danh sách đã tạo", lambda: self.set_posting_step(3)),
            )
        )
        self.job_posts = QComboBox()
        self.job_posts.currentIndexChanged.connect(self.update_post_choice_preview)
        choose.addLayout(
            row(
                QLabel("Bài muốn đăng"),
                self.job_posts,
                button("Soạn / sửa bài đang chọn", lambda: self.guard(self.edit_chosen_article)),
            )
        )
        self.post_choice_preview = QTextBrowser()
        self.post_choice_preview.setOpenExternalLinks(False)
        choose.addWidget(self.post_choice_preview, 1)
        self.batch_name = QLineEdit()
        self.batch_name.setPlaceholderText("Tên đợt đăng (không bắt buộc), ví dụ: Tuyển kỹ sư tháng 11")
        self.audience_mode = QComboBox()
        self.audience_mode.addItems(["Một nhóm", "Nhiều nhóm", "Theo nhãn nhóm"])
        self.job_groups = QComboBox()
        self.audience_tag = QComboBox()
        self.audience_mode.currentIndexChanged.connect(self.refresh_audience)
        self.audience_tag.currentIndexChanged.connect(self.refresh_audience)
        audience.addLayout(
            row(
                QLabel("Đăng ở đâu?"),
                self.audience_mode,
                self.job_groups,
                self.audience_tag,
                button("Thêm nhóm", lambda: self.tabs.setCurrentIndex(1)),
            )
        )
        self.audience_list = QListWidget()
        self.audience_list.itemChanged.connect(self.update_audience_count)
        audience.addWidget(self.audience_list, 1)
        audience.addWidget(
            hint(
                "Tích các nhóm muốn đăng. Chọn theo nhãn để chọn nhanh nhiều nhóm; có thể bỏ tích nhóm không cần."
            )
        )
        self.select_all_groups = button("Chọn tất cả", lambda: self.check_audience(True))
        self.clear_groups = button("Bỏ chọn tất cả", lambda: self.check_audience(False))
        self.audience_count = hint("")
        audience.addLayout(row(self.audience_count, self.select_all_groups, self.clear_groups))
        self.review_summary = hint("")
        review.addWidget(self.review_summary)
        self.review_preview = QTextBrowser()
        self.review_preview.setOpenExternalLinks(False)
        review.addWidget(self.review_preview, 1)
        self.review_groups = QListWidget()
        self.review_groups.setMaximumHeight(90)
        review.addWidget(self.review_groups)
        self.review_images = QListWidget()
        self.review_images.setIconSize(QSize(55, 55))
        self.review_images.setMaximumHeight(85)
        review.addWidget(self.review_images)
        review.addWidget(
            hint(
                "Kiểm tra nội dung, ảnh và các nhóm ở trên. Facebook có thể hiển thị định dạng khác bản xem trước."
            )
        )
        self.auto_send = QCheckBox("Tự bấm Đăng và chuyển sang nhóm tiếp theo")
        self.auto_send.setChecked(True)
        self.group_delay = QSpinBox()
        self.group_delay.setRange(5, 300)
        self.group_delay.setValue(15)
        self.group_delay.setSuffix(" giây giữa các nhóm")
        review.addLayout(row(self.auto_send, self.group_delay))
        review.addWidget(self.batch_name)
        review.addWidget(button("Lưu đợt đăng để chạy sau", lambda: self.guard(self.save_reviewed_batch)))
        self.batch_filter = QComboBox()
        self.batch_filter.addItem("Tất cả lượt đăng", None)
        self.batch_filter.currentIndexChanged.connect(self.batch_changed)
        run.addLayout(row(QLabel("Đợt đăng đang xem"), self.batch_filter))
        self.queue_progress = hint("Chọn một đợt đã tạo, hoặc Quay lại để tạo đợt đăng mới.")
        run.addWidget(self.queue_progress)
        self.queue_progress_bar = QProgressBar()
        self.queue_progress_bar.setRange(0, 1)
        run.addWidget(self.queue_progress_bar)
        self.current_action = hint("Sẵn sàng. Ứng dụng chỉ đăng sau khi bạn bấm Bắt đầu.")
        run.addWidget(self.current_action)
        self.problem_panel = QWidget()
        problems = QVBoxLayout(self.problem_panel)
        self.problem_help = hint("")
        problems.addWidget(self.problem_help)
        problems.addLayout(
            row(
                self.browser_button("Mở Facebook để kiểm tra", "login"),
                self.browser_button("Mở nhóm đang chọn", "open_group"),
            )
        )
        self.problem_details = QTextBrowser()
        self.problem_details.setMaximumHeight(110)
        self.problem_details.hide()
        details = button(
            "Xem chi tiết lỗi", lambda: self.problem_details.setVisible(not self.problem_details.isVisible())
        )
        problems.addWidget(details)
        problems.addWidget(self.problem_details)
        run.addWidget(self.problem_panel)
        self.problem_panel.hide()
        self.begin_posting_button = button(
            "Bắt đầu tự đăng", lambda: self.guard(self.start_posting_queue), True
        )
        self.posting_mode_hint = hint("")
        run.addWidget(self.posting_mode_hint)
        self.auto_send.toggled.connect(self.update_posting_mode)
        self.update_posting_mode()
        self.browser_buttons.append(self.begin_posting_button)
        run.addLayout(row(self.begin_posting_button, button("Tạm dừng", self.pause_posting_queue)))
        self.manual_posting_tools = QWidget()
        manual = QVBoxLayout(self.manual_posting_tools)
        toggle = button("Tùy chọn khác: xử lý bằng tay", lambda: None)
        self.manual_tools_toggle = toggle
        toggle.setCheckable(True)
        toggle.toggled.connect(self.manual_posting_tools.setVisible)
        run.addWidget(toggle)
        run.addWidget(self.manual_posting_tools)
        following = button("Tôi đã đăng · sang nhóm sau", lambda: self.guard(self.complete_queue_job))
        skip = button("Bỏ qua nhóm này", lambda: self.guard(self.skip_queue_job))
        self.browser_buttons.extend([following, skip])
        manual.addLayout(
            row(
                following,
                skip,
                self.browser_button("Điền bài đang mở", "fill"),
                button("Đăng bản đang mở", lambda: self.guard(self.publish_open_draft)),
            )
        )
        self.manual_posting_tools.hide()
        self.refresh_audience()
        self.set_posting_step(0)

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
        if hasattr(self, "manual_tools_toggle"):
            self.manual_tools_toggle.setChecked(not automatic)
        if hasattr(self, "posting_steps") and self.posting_steps.currentIndex() == 2:
            self.posting_next.setText("Bắt đầu đăng" if automatic else "Chuẩn bị bài")
        self.begin_posting_button.setText("Bắt đầu tự đăng" if automatic else "Chỉ chuẩn bị bài")
        self.posting_mode_hint.setText(
            "TỰ ĐĂNG: mở nhóm → dán bài → tải ảnh → bấm Đăng. Tự cập nhật kết quả và chuyển nhóm tiếp theo."
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
        duplicates = {job["group_name"] for job in self.store.post_duplicates(post_id, group_ids)}
        if (
            duplicates
            and QMessageBox.question(
                self,
                "Bài đã có lịch sử ở một số nhóm",
                "Cùng nội dung và ảnh đã có lượt ở: "
                + ", ".join(sorted(duplicates))
                + ".\nVẫn tạo danh sách mới?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        audience = (
            self.audience_tag.currentText() if self.audience_mode.currentIndex() == 2 else "Tự chọn nhóm"
        )
        batch_id = self.store.create_batch(
            post_id, group_ids, self.batch_name.text(), audience, allow_duplicate=bool(duplicates)
        )
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
        if self.batch_filter.currentData() is not None:
            self.store.set_preference("last_batch", self.batch_filter.currentData())
        self.pause_posting_queue(announce=False)
        self.refresh_jobs()
        self.update_queue_progress()

    def update_queue_progress(self):
        batch_id = self.batch_filter.currentData()
        jobs = self.store.batch_jobs(batch_id) if batch_id is not None else []
        if not jobs:
            self.queue_progress_bar.setRange(0, 1)
            self.queue_progress_bar.setValue(0)
            self.queue_progress.setText(
                "Chọn một danh sách để bắt đầu. Bạn có thể lưu nhiều danh sách cho nhiều bài khác nhau."
            )
            return
        done = sum(
            job["status"] in {"submitted", "pending", "published", "rejected", "removed", "skipped"}
            for job in jobs
        )
        self.queue_progress_bar.setRange(0, len(jobs))
        self.queue_progress_bar.setValue(done)
        errors = sum(job["status"] in {"error", "uncertain"} for job in jobs)
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
            if job["status"] in {"uncertain", "sending"}:
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

    def start_posting_queue(self, confirmed=False):
        if self.monitor_running:
            raise ValueError("Bấm Dừng kiểm tra và chờ thao tác hoàn tất trước khi đăng bài.")
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
        if automatic and not confirmed:
            jobs = [entry for entry in self.store.batch_jobs(batch_id) if entry["status"] in READY]
            names = "\n".join(f"• {entry['group_name']}" for entry in jobs)
            if (
                QMessageBox.question(
                    self,
                    "Xác nhận tự gửi bài",
                    f"Bài: {job['title']}\nNhóm sắp đăng: {job['group_name']}\nDanh sách có {len(jobs)} nhóm còn lại:\n"
                    + names
                    + "\n\nỨng dụng tự cập nhật kết quả gửi và chuyển nhóm tiếp theo. Bạn đã kiểm tra bài, ảnh và các nhóm này?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
        if automatic:
            self.authorized_auto_batch = batch_id
        self.set_posting_step(3)
        self.store.set_preference("last_batch", batch_id)
        self.queue_auto = automatic
        self.queue_batch_id = batch_id
        self.queue_active = True
        self.dispatch_queue_job(job)

    def dispatch_queue_job(self, job):
        self.queue_current_job = job
        self.queue_current_total = len(self.store.batch_jobs(job["batch_id"]))
        self.refresh_batches(job["batch_id"])
        self.history_search.clear()
        self.refresh_jobs(job["id"])
        self.problem_panel.hide()
        self.current_action.setText(
            f"Nhóm {job['position'] + 1}/{len(self.store.batch_jobs(job['batch_id']))}: {job['group_name']} · Đang chuẩn bị"
        )
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
            self.current_action.setText(
                "Đã hoàn tất đợt đăng. Xem kết quả từng nhóm bên dưới hoặc vào Bài đã đăng để kiểm tra duyệt."
            )
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
        if (
            action in {"publish", "publish_current"}
            and result.get("sent")
            and self.queue_active
            and self.queue_auto
        ):
            self.queue_timer.start(self.group_delay.value() * 1000)
            self.statusBar().showMessage(
                f"Đã gửi. Tự chuyển nhóm sau {self.group_delay.value()} giây; có thể Tạm dừng.", 30000
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
                    source="manual_sent",
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
            self.store.update_job(
                job["id"], source="manual_sent", status=status, url=url, note=self.job_note.text()
            )
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
