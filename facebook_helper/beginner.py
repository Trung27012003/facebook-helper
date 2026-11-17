"""Guided posting and recoverable drafts; neither feature publishes on startup."""

import json
import uuid
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .formatting import article_html
from .storage import now
from .widgets import button, hint, row


class BeginnerMixin:
    def build_quick_start(self):
        self.quick_start = QWidget()
        layout = QVBoxLayout(self.quick_start)
        layout.addWidget(
            hint(
                "Lần đầu sử dụng? Làm lần lượt: đăng nhập Facebook → thêm nhóm → soạn bài. Không cần cài đặt thêm."
            )
        )
        layout.addLayout(
            row(
                button("1. Đăng nhập Facebook", lambda: self.guard(lambda: self.run_browser("login"))),
                button("2. Thêm nhóm", lambda: self.tabs.setCurrentIndex(1)),
                button("3. Soạn bài", self.finish_quick_start, True),
                button("Ẩn hướng dẫn", self.hide_quick_start),
            )
        )
        self.quick_start.hide()
        return self.quick_start

    def finish_quick_start(self):
        self.hide_quick_start()
        self.tabs.setCurrentIndex(0)

    def hide_quick_start(self):
        self.quick_start.hide()
        self.store.set_preference("quick_start_done", "1")

    def setup_drafts(self):
        self.active_draft_id = None
        self.draft_timer = QTimer(self)
        self.draft_timer.setSingleShot(True)
        self.draft_timer.setInterval(1200)
        self.draft_timer.timeout.connect(self.autosave_draft)
        self.update_draft_notice()

    def stored_drafts(self):
        return json.loads(self.store.preference("editor_drafts", "{}"))

    def update_draft_notice(self):
        drafts = self.stored_drafts()
        count = len([key for key in drafts if key != getattr(self, "active_draft_id", None)])
        self.draft_recovery.setVisible(count > 0)
        self.draft_recovery_text.setText(
            f"Có {count} bản nháp tự lưu chưa hoàn tất. Bạn có thể khôi phục để tiếp tục soạn."
        )

    def autosave_draft(self):
        self.draft_timer.stop()
        if not self.dirty or self.closing:
            return True
        try:
            drafts = self.stored_drafts()
            draft_id = self.active_draft_id or uuid.uuid4().hex
            drafts[draft_id] = {
                "post_id": self.post_id,
                "post_uid": self.store.post(self.post_id)["uid"] if self.post_id is not None else None,
                "title": self.title.text(),
                "html": self.content.toHtml(),
                "plain": self.content.toPlainText(),
                "tags": self.tags.text(),
                "images": [
                    self.images.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.images.count())
                ],
                "saved_at": now(),
            }
            self.store.set_preference("editor_drafts", json.dumps(drafts, ensure_ascii=False))
            self.active_draft_id = draft_id
            self.autosave_note.setText(
                "Đã tự lưu bản nháp · Bấm Lưu bài khi sẵn sàng đưa vào danh sách đăng."
            )
            self.update_draft_notice()
            return True
        except Exception:
            self.autosave_note.setText(
                "Chưa tự lưu được nháp. Bấm Lưu bài hoặc kiểm tra dung lượng ổ đĩa trước khi đóng."
            )
            return False

    def clear_active_draft(self):
        if not hasattr(self, "draft_timer"):
            return
        self.draft_timer.stop()
        if self.active_draft_id:
            drafts = self.stored_drafts()
            drafts.pop(self.active_draft_id, None)
            self.store.set_preference("editor_drafts", json.dumps(drafts, ensure_ascii=False))
        self.active_draft_id = None
        self.update_draft_notice()
        self.autosave_note.setText("Bản đang soạn được tự lưu sau khi bạn ngừng nhập một lúc.")

    def recover_draft(self):
        drafts = self.stored_drafts()
        options = sorted(
            ((key, draft) for key, draft in drafts.items() if key != self.active_draft_id),
            key=lambda pair: pair[1]["saved_at"],
            reverse=True,
        )
        if not options:
            return
        labels = [
            f"{i + 1}. {d['title'] or 'Bài chưa đặt tên'} · {datetime.fromisoformat(d['saved_at']).astimezone().strftime('%d/%m/%Y %H:%M')}"
            for i, (_, d) in enumerate(options)
        ]
        if len(options) > 1:
            choice, ok = QInputDialog.getItem(
                self, "Chọn bản nháp cần tiếp tục", "Bản nháp đã tự lưu:", labels, 0, False
            )
            if not ok:
                return
            key, draft = options[labels.index(choice)]
        else:
            key, draft = options[0]
        for image in draft["images"]:
            self.store.asset(image)
        if not self.confirm_discard():
            return
        self.loading = True
        # SQLite can reuse a deleted numeric ID. Only a persistent identity can prove
        # this is still the same post; older drafts without it recover as copies.
        self.post_id = next(
            (
                p["id"]
                for p in self.store.posts()
                if p["id"] == draft["post_id"] and draft.get("post_uid") and p["uid"] == draft["post_uid"]
            ),
            None,
        )
        self.title.setText(draft["title"])
        self.content.setHtml(draft["html"])
        self.tags.setText(draft["tags"])
        self.images.clear()
        for image in draft["images"]:
            self.add_image_item(image)
        self.loading = False
        self.active_draft_id = key
        self.mark_dirty()
        self.update_draft_notice()
        self.tabs.setCurrentIndex(0)

    def discard_recovery_drafts(self):
        if (
            QMessageBox.question(
                self,
                "Bỏ các bản nháp chưa hoàn tất",
                "Xóa các bản nháp chưa khôi phục? Các bài đã bấm Lưu bài vẫn được giữ.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        drafts = self.stored_drafts()
        keep = {self.active_draft_id: drafts[self.active_draft_id]} if self.active_draft_id in drafts else {}
        self.store.set_preference("editor_drafts", json.dumps(keep, ensure_ascii=False))
        self.update_draft_notice()

    def init_posting_steps(self, layout):
        self.posting_step_label = QLabel()
        self.posting_step_label.setWordWrap(True)
        self.posting_step_label.setStyleSheet("font-size:18px;font-weight:700;padding:8px 0;")
        layout.addWidget(self.posting_step_label)
        self.posting_steps = QStackedWidget()
        pages = []
        for _ in range(4):
            page = QWidget()
            pages.append(QVBoxLayout(page))
            self.posting_steps.addWidget(page)
        layout.addWidget(self.posting_steps, 1)
        self.posting_back = button(
            "Quay lại",
            lambda: self.guard(
                lambda: self.set_posting_step(
                    0 if self.posting_steps.currentIndex() == 3 else self.posting_steps.currentIndex() - 1
                )
            ),
        )
        self.posting_next = button("Tiếp tục: Chọn nhóm", lambda: self.guard(self.posting_next_step), True)
        self.posting_navigation = row(self.posting_back, self.posting_next)
        self.run_layout = pages[3]
        return pages

    def set_posting_step(self, index):
        if index < 3 and (self.busy or self.queue_active or getattr(self, "monitor_running", False)):
            raise ValueError("Tạm dừng và chờ thao tác hiện tại hoàn tất trước khi thay đổi bài hoặc nhóm.")
        self.posting_steps.setCurrentIndex(index)
        names = ["1. Chọn bài", "2. Chọn nơi đăng", "3. Xem lại", "4. Đăng và xem kết quả"]
        self.posting_step_label.setText(
            "  →  ".join(f"【{name}】" if i == index else name for i, name in enumerate(names))
        )
        self.posting_back.setVisible(index > 0)
        self.posting_back.setText("Tạo đợt đăng mới" if index == 3 else "Quay lại")
        self.posting_next.setVisible(index < 3)
        self.posting_next.setText(
            [
                "Tiếp tục: Chọn nhóm",
                "Tiếp tục: Xem lại",
                "Bắt đầu đăng" if self.auto_send.isChecked() else "Chuẩn bị bài",
                "",
            ][index]
        )
        if index == 0:
            self.update_post_choice_preview()

    def update_post_choice_preview(self, *args):
        if not hasattr(self, "post_choice_preview"):
            return
        post_id = self.job_posts.currentData()
        if post_id is None:
            self.post_choice_preview.setPlainText(
                "Chưa có bài đã lưu. Vào Soạn bài, nhập nội dung rồi bấm Lưu bài."
            )
        else:
            post = self.store.post(post_id)
            self.post_choice_preview.setHtml(article_html(post["html"], post["tags"]))

    def edit_chosen_article(self):
        post_id = self.job_posts.currentData()
        if post_id is not None and post_id != self.post_id:
            item = next(
                (
                    self.post_list.item(i)
                    for i in range(self.post_list.count())
                    if self.post_list.item(i).data(Qt.ItemDataRole.UserRole) == post_id
                ),
                None,
            )
            if item is None:
                raise ValueError("Bài không còn trong danh sách. Làm mới hoặc tạo bài mới trước nhé.")
            self.load_post(item)
            if self.post_id != post_id:
                return
        self.tabs.setCurrentIndex(0)

    def posting_signature(self):
        post_id = self.job_posts.currentData()
        if post_id is None:
            raise ValueError("Chọn bài đã lưu trước khi tiếp tục.")
        if self.dirty and self.post_id == post_id:
            raise ValueError("Bài đang có chỉnh sửa chưa lưu. Quay lại Soạn bài và bấm Lưu bài trước nhé.")
        groups = [
            self.store.db.execute("SELECT * FROM groups WHERE id=?", (key,)).fetchone()
            for key in self.selected_group_ids()
        ]
        if not groups or any(g is None for g in groups):
            raise ValueError("Chọn ít nhất một nhóm còn tồn tại trước nhé.")
        return json.dumps(
            [self.store.post(post_id), [dict(g) for g in groups]], sort_keys=True, ensure_ascii=False
        )

    def posting_next_step(self):
        step = self.posting_steps.currentIndex()
        if step == 0:
            if self.job_posts.currentData() is None:
                raise ValueError("Chưa có bài đã lưu. Vào Soạn bài và bấm Lưu bài trước nhé.")
            self.set_posting_step(1)
        elif step == 1:
            self.review_signature = self.posting_signature()
            post, groups = json.loads(self.review_signature)
            self.review_preview.setHtml(article_html(post["html"], post["tags"]))
            self.review_images.clear()
            for index, image in enumerate(post["images"]):
                self.store.asset(image)
                self.review_images.addItem(
                    QListWidgetItem(QIcon(str(self.store.root / image)), f"Ảnh {index + 1}")
                )
            self.review_summary.setText(
                f"Bài: {post['title']} · {len(post['images'])} ảnh · {len(groups)} nhóm"
            )
            self.review_groups.clear()
            self.review_groups.addItems([g["name"] for g in groups])
            self.set_posting_step(2)
        elif step == 2:
            batch = self.save_reviewed_batch()
            if batch is not None:
                self.start_posting_queue(confirmed=True)

    def save_reviewed_batch(self):
        if self.posting_signature() != self.review_signature:
            raise ValueError(
                "Bài hoặc nhóm đã thay đổi. Quay lại Chọn nơi đăng và Xem lại trước khi bắt đầu."
            )
        batch = self.create_posting_batch()
        if batch is not None:
            self.set_posting_step(3)
            self.current_action.setText(
                "Đã lưu đợt đăng. Bấm Bắt đầu khi muốn chạy; có thể lưu thêm đợt khác trước."
            )
        return batch

    def post_this_article(self):
        if self.busy or self.queue_active or self.monitor_running:
            raise ValueError("Tạm dừng và chờ thao tác hiện tại hoàn tất trước khi đăng bài khác.")
        if self.post_id is None or self.dirty:
            self.save_post()
        self.job_posts.setCurrentIndex(self.job_posts.findData(self.post_id))
        self.set_posting_step(0)
        self.tabs.setCurrentIndex(2)
