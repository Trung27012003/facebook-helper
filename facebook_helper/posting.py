"""Audience selection and sequential posting, with one browser operation at a time."""

from PySide6.QtCore import QDate, QSize, Qt, QTimer
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

from .choices import CheckList, CheckPicker
from .manager import local_date
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
        self.audience_mode.addItems(["Một nhóm", "Nhiều nhóm", "Theo nhãn nhóm", "Theo vị trí tuyển dụng"])
        self.job_groups = QComboBox()
        self.audience_tag = CheckPicker("Chọn một hoặc nhiều nhãn")
        self.audience_positions = CheckPicker("Chọn một hoặc nhiều vị trí")
        self.audience_mode.currentIndexChanged.connect(self.refresh_audience)
        self.audience_tag.changed.connect(self.refresh_audience)
        self.audience_positions.changed.connect(self.refresh_audience)
        audience.addLayout(
            row(
                QLabel("Đăng ở đâu?"),
                self.audience_mode,
                self.job_groups,
                self.audience_tag,
                self.audience_positions,
                button("Thêm nhóm", lambda: self.tabs.setCurrentIndex(2)),
            )
        )
        self.audience_list = CheckList()
        self.audience_list.itemChanged.connect(self.update_audience_count)
        audience.addWidget(self.audience_list, 1)
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
        self.batch_filter.setMinimumContentsLength(20)
        self.batch_filter.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.batch_filter.addItem("Tất cả lượt đăng", None)
        self.batch_filter.currentIndexChanged.connect(self.batch_changed)
        self.new_batch_button = button("Đợt đăng mới", lambda: self.guard(lambda: self.set_posting_step(0)))
        self.results_button = button("Bài đã đăng", self.show_batch_results)
        batch_row = row(QLabel("Đợt đăng"), self.batch_filter, self.new_batch_button, self.results_button)
        batch_row.setStretch(1, 1)
        run.addLayout(batch_row)
        self.run_state = QLabel("Chưa bắt đầu")
        self.queue_progress = hint("Chọn một đợt đã tạo, hoặc Quay lại để tạo đợt đăng mới.")
        progress_row = row(self.run_state, self.queue_progress)
        progress_row.addStretch()
        run.addLayout(progress_row)
        self.queue_progress_bar = QProgressBar()
        self.queue_progress_bar.setRange(0, 1)
        self.queue_progress_bar.setTextVisible(False)
        self.queue_progress_bar.setFixedHeight(8)
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
        self.mode_badge = QLabel("")
        self.auto_send.toggled.connect(self.update_posting_mode)
        self.update_posting_mode()
        self.browser_buttons.append(self.begin_posting_button)
        self.pause_posting_button = button("Tạm dừng", self.pause_posting_queue)
        self.pause_posting_button.setStyleSheet("background:#fef3c7;color:#92400e;font-weight:600;")
        self.manual_posting_tools = QWidget()
        manual = QVBoxLayout(self.manual_posting_tools)
        toggle = button("Thao tác khác", lambda: None)
        self.manual_tools_toggle = toggle
        toggle.setCheckable(True)
        toggle.toggled.connect(self.manual_posting_tools.setVisible)
        actions = row(self.begin_posting_button, self.pause_posting_button, self.mode_badge)
        actions.addStretch()
        actions.addWidget(toggle)
        run.addLayout(actions)
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
        self.mode_badge.setText("Tự đăng" if automatic else "Chỉ chuẩn bị")
        if hasattr(self, "history"):
            self.update_queue_progress()

    def show_batch_results(self):
        view = self.post_manager
        batch_id = self.batch_filter.currentData()
        view.refresh()
        view.batch.setCurrentIndex(max(0, view.batch.findData(batch_id)))
        view.keyword.clear()
        dates = [
            local_date(j["activity_at"]).date()
            for j in self.store.posting_register()
            if j["batch_id"] == batch_id
        ]
        if dates:
            first, last = min(dates), max(dates)
            view.start.setDate(QDate(first.year, first.month, first.day))
            view.end.setDate(QDate(last.year, last.month, last.day))
        else:
            view.start.setDate(QDate.currentDate())
            view.end.setDate(QDate.currentDate())
        view.search()
        self.tabs.setCurrentIndex(4)

    def refresh_audience(self, *args):
        if not hasattr(self, "audience_list"):
            return
        old = {
            self.audience_list.item(i).data(Qt.ItemDataRole.UserRole): self.audience_list.item(i).checkState()
            == Qt.CheckState.Checked
            for i in range(self.audience_list.count())
        }
        mode = self.audience_mode.currentIndex()
        self.job_groups.setVisible(mode == 0)
        self.audience_tag.setVisible(mode == 2)
        self.audience_positions.setVisible(mode == 3)
        self.audience_list.setVisible(mode != 0)
        self.select_all_groups.setVisible(mode != 0)
        self.clear_groups.setVisible(mode != 0)
        criteria = (
            mode,
            tuple(self.audience_tag.checked_data())
            if mode == 2
            else tuple(self.audience_positions.checked_data())
            if mode == 3
            else (),
        )
        same = criteria == getattr(self, "audience_criteria", None)
        self.audience_criteria = criteria
        if mode == 2:
            groups = self.store.groups_for_selection(tags=self.audience_tag.labels())
        elif mode == 3:
            groups = self.store.groups_for_selection(position_ids=self.audience_positions.checked_data())
        else:
            groups = self.store.groups()
        self.audience_list.blockSignals(True)
        self.audience_list.clear()
        for group in groups:
            item = QListWidgetItem(group["name"] + (f" · {group['category']}" if group["category"] else ""))
            item.setData(Qt.ItemDataRole.UserRole, group["id"])
            item.setToolTip("Vị trí: " + (", ".join(group["position_names"]) or "Chưa gán vị trí"))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = old.get(group["id"], mode in (2, 3)) if same else mode in (2, 3)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.audience_list.addItem(item)
        self.audience_list.blockSignals(False)
        self.update_audience_count()

    def refresh_audience_tags(self):
        for picker, options in (
            (self.audience_tag, [(t.casefold(), t) for t in self.store.group_tags()]),
            (self.audience_positions, [(p["id"], p["name"]) for p in self.store.positions()]),
        ):
            picker.blockSignals(True)
            picker.set_items(options)
            picker.blockSignals(False)
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
        mode = self.audience_mode.currentIndex()
        if mode == 2 and not self.audience_tag.checked_data():
            self.audience_count.setText("Chọn nhãn để xem các nhóm phù hợp")
        elif mode == 3 and not self.audience_positions.checked_data():
            self.audience_count.setText("Chọn vị trí để xem các nhóm phù hợp")
        else:
            self.audience_count.setText(f"Đã chọn {len(self.selected_group_ids())} nhóm")

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
            self.audience_tag.currentText()
            if self.audience_mode.currentIndex() == 2
            else "Vị trí: " + self.audience_positions.currentText()
            if self.audience_mode.currentIndex() == 3
            else "Tự chọn nhóm"
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
        done = sum(job["status"] in SENT for job in jobs)
        errors = sum(
            job["status"] in {"error", "uncertain"}
            or (job["status"] == "sending" and not self.busy and not self.queue_active)
            for job in jobs
        )
        complete = bool(jobs) and done == len(jobs)
        blocked = any(job["status"] in {"uncertain", "sending"} for job in jobs)
        self.queue_progress_bar.setRange(0, max(1, len(jobs)))
        self.queue_progress_bar.setValue(done)
        self.queue_progress.setText(
            f"{done}/{len(jobs)} nhóm" + (f" · {errors} cần xem lại" if errors else "")
        )
        state = (
            "Đang đăng"
            if self.queue_active
            else "Hoàn tất"
            if complete
            else "Cần xem lại"
            if errors
            else "Chưa bắt đầu"
            if not done
            else "Tạm dừng"
        )
        color, background = (
            ("#166534", "#dcfce7")
            if complete
            else ("#1d4ed8", "#dbeafe")
            if self.queue_active
            else ("#92400e", "#fef3c7")
            if errors
            else ("#475569", "#e8edf5")
        )
        self.run_state.setText(state if jobs else "Chưa có đợt đăng")
        self.run_state.setStyleSheet(
            f"color:{color};background:{background};font-weight:600;padding:6px 10px;border-radius:6px;"
        )
        self.begin_posting_button.setVisible(bool(jobs) and not complete and not self.queue_active)
        self.begin_posting_button.setEnabled(
            bool(jobs) and not complete and not self.busy and not blocked and not self.queue_active
        )
        self.begin_posting_button.setText(
            ("Tiếp tục đăng" if done else "Bắt đầu đăng") if self.auto_send.isChecked() else "Chuẩn bị bài"
        )
        self.pause_posting_button.setVisible(self.queue_active)
        self.new_batch_button.setEnabled(not self.busy and not self.queue_active)
        self.results_button.setEnabled(bool(jobs))
        self.current_action.setVisible(bool(self.busy or self.queue_active))
        self.mode_badge.setVisible(bool(jobs) and not complete)
        self.manual_tools_toggle.setVisible(bool(jobs) and not complete)
        if complete or not jobs:
            self.manual_tools_toggle.setChecked(False)
        elif not self.auto_send.isChecked():
            self.manual_tools_toggle.setChecked(True)
        for widget in self.browser_buttons:
            if widget is not self.begin_posting_button:
                widget.setEnabled(not self.busy and not (self.queue_active and self.queue_auto))
        if hasattr(self, "settings_login_button"):
            self.settings_login_button.setEnabled(not self.busy and not self.queue_active)
        self.resume_button.setEnabled(not self.busy and not self.queue_active)
        self.resume_button.setVisible(
            any(
                j["batch_id"] is not None and j["status"] in READY | {"uncertain", "sending"}
                for j in self.store.jobs()
            )
        )
        self.update_editor_actions()
        for widget, primary in ((self.results_button, complete), (self.new_batch_button, not jobs)):
            if widget.property("primary") != primary:
                widget.setProperty("primary", primary)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

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
            self.current_action.setText("Đã hoàn tất đợt đăng.")
            self.statusBar().showMessage("Đã hoàn tất đợt đăng.", 20000)
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
