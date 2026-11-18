"""Coordinate read-only checks with the single posting worker."""

from PySide6.QtCore import QTimer

TRACKABLE = {"submitted", "pending", "published", "uncertain", "rejected", "removed"}


class TrackingMixin:
    def setup_tracking(self):
        self.monitor_ids = []
        self.monitor_running = False
        self.monitor_total = 0
        self.monitor_done = 0
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.periodic_check)
        self.configure_tracking()

    def configure_tracking(self):
        # Approval checking is no longer part of the posting workflow.
        self.monitor_timer.stop()
        if self.store.preference("monitor_enabled") == "1":
            self.store.set_preference("monitor_enabled", "0")

    def periodic_check(self):
        return

    def start_checks(self, ids):
        if self.busy or self.queue_active or self.monitor_running:
            raise ValueError("Tạm dừng đăng bài và chờ thao tác hiện tại xong trước khi kiểm tra trạng thái.")
        jobs = [self.store.job(job_id) for job_id in dict.fromkeys(ids)]
        self.monitor_ids = [j["id"] for j in jobs if j["status"] in TRACKABLE]
        if not self.monitor_ids:
            raise ValueError("Chọn bài đã gửi hoặc chưa rõ kết quả. Bài chưa gửi không cần kiểm tra duyệt.")
        self.monitor_total = len(self.monitor_ids)
        self.monitor_done = 0
        self.monitor_running = True
        self.dispatch_check()

    def dispatch_check(self):
        if self.busy:
            return
        if self.closing or not self.monitor_running or not self.monitor_ids:
            self.monitor_running = False
            return
        job = self.store.job(self.monitor_ids.pop(0))
        self.busy = True
        for widget in self.browser_buttons:
            widget.setEnabled(False)
        self.statusBar().showMessage(
            f"Đang kiểm tra {self.monitor_done + 1}/{self.monitor_total}: {job['group_name']}. Dừng kiểm tra để hủy các bài còn lại."
        )
        self.browser.submit("check_status", {**job, "job_id": job["id"]})

    def complete_check(self, result):
        self.store.record_check(
            result["job_id"],
            result.get("outcome", "unknown"),
            result.get("message", "Chưa xác minh được"),
            result.get("url", ""),
        )
        self.monitor_done += 1
        self.refresh_jobs()
        self.post_manager.refresh()
        if self.monitor_running and self.monitor_ids and not self.closing:
            QTimer.singleShot(1500, lambda: self.guard(self.dispatch_check))
        else:
            self.monitor_running = False
            self.statusBar().showMessage(
                f"Đã kiểm tra {self.monitor_done}/{self.monitor_total} bài. Xem cột Kết quả kiểm tra và Lịch sử trạng thái."
            )

    def stop_checks(self):
        self.monitor_running = False
        self.monitor_ids.clear()
        self.statusBar().showMessage("Đã dừng kiểm tra. Bài đang đọc (nếu có) sẽ hoàn tất.")

    def resume_saved_queue(self):
        if self.busy or self.monitor_running:
            raise ValueError("Chờ thao tác hiện tại hoàn tất trước khi tiếp tục đăng.")
        candidates = [
            b
            for b in self.store.batches()
            if any(
                j["status"] in {"draft", "prepared", "error", "sending", "uncertain"}
                for j in self.store.batch_jobs(b["id"])
            )
        ]
        selected = self.batch_filter.currentData()
        candidate = next(
            (b for b in candidates if b["id"] == selected), candidates[0] if candidates else None
        )
        if candidate is None:
            self.statusBar().showMessage("Không còn danh sách cần tiếp tục.", 10000)
            return
        self.refresh_batches(candidate["id"])
        self.store.set_preference("last_batch", candidate["id"])
        self.refresh_jobs()
        self.set_posting_step(3)
        self.tabs.setCurrentIndex(3)
        self.statusBar().showMessage(
            "Đã mở danh sách còn lại. Kiểm tra lượt chưa rõ kết quả rồi bấm Bắt đầu / tiếp tục.", 15000
        )
