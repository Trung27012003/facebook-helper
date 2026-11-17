"""Asynchronous public release checks; downloads open only after user acceptance."""

import json
import re
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import __version__

REPO = "Trung27012003/facebook-helper"
CHECK_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
SETUP_NAME = "FacebookHelper-Setup-x64.exe"


def version_parts(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?\d{1,4}\.\d{1,4}\.\d{1,4}", value):
        raise ValueError("Phiên bản không hợp lệ")
    return tuple(int(n) for n in value.removeprefix("v").split("."))


def latest_installer(data, current=__version__):
    if not isinstance(data, dict) or data.get("draft") or data.get("prerelease"):
        return None
    tag = data.get("tag_name", "")
    if version_parts(tag) <= version_parts(current):
        return None
    expected = f"https://github.com/{REPO}/releases/download/{tag}/{SETUP_NAME}"
    assets = data.get("assets", [])
    matches = [
        a
        for a in assets
        if isinstance(a, dict)
        and a.get("name") == SETUP_NAME
        and a.get("browser_download_url") == expected
        and a.get("state") == "uploaded"
        and isinstance(a.get("size"), int)
        and a["size"] > 0
    ]
    return {"version": tag.removeprefix("v"), "url": expected} if len(matches) == 1 else None


class UpdateChecker(QObject):
    available = Signal(object)
    status = Signal(str)

    def __init__(self, store, parent=None, manager=None):
        super().__init__(parent)
        self.store = store
        self.manager = manager or QNetworkAccessManager(self)
        self.reply = None
        self.stopped = False
        self.timer = QTimer(self)
        self.timer.setInterval(6 * 60 * 60 * 1000)
        self.timer.timeout.connect(lambda: self.check(False))

    def start(self):
        self.timer.start()
        QTimer.singleShot(5000, lambda: self.check(False) if not self.stopped else None)

    def check(self, manual=False):
        if self.stopped or self.reply is not None:
            return
        if not manual:
            try:
                last = datetime.fromisoformat(self.store.preference("update_last_check"))
                if (datetime.now(timezone.utc) - last).total_seconds() < 24 * 3600:
                    return
            except (ValueError, TypeError):
                pass
        request = QNetworkRequest(QUrl(CHECK_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", f"FacebookHelper/{__version__}".encode())
        request.setTransferTimeout(10000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self.reply = self.manager.get(request)
        self.reply.finished.connect(lambda: self.complete(manual))
        self.status.emit("Đang kiểm tra cập nhật…")

    def complete(self, manual):
        reply = self.reply
        self.reply = None
        if reply is None:
            return
        try:
            if self.stopped:
                return
            if (
                reply.error() != QNetworkReply.NetworkError.NoError
                or reply.bytesAvailable() > 2 * 1024 * 1024
            ):
                self.status.emit("Chưa kiểm tra được cập nhật")
                return
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            release = latest_installer(data)
            if release is None and version_parts(data.get("tag_name", "")) > version_parts(__version__):
                self.status.emit("Bản mới đang chuẩn bị bộ cài; bạn có thể kiểm tra lại sau")
                return
            self.store.set_preference("update_last_check", datetime.now(timezone.utc).isoformat())
            if release:
                release["manual"] = manual
                self.status.emit("Có bản mới " + release["version"])
                self.available.emit(release)
            else:
                self.status.emit("Đang dùng bản mới nhất" if manual else "")
        except Exception:
            self.status.emit("Chưa kiểm tra được cập nhật")
        finally:
            reply.deleteLater()

    def stop(self):
        self.stopped = True
        self.timer.stop()
        if self.reply is not None:
            self.reply.abort()
