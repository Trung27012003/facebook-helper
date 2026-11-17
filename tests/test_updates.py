import json
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QByteArray, QObject, Signal
from PySide6.QtNetwork import QNetworkReply

from facebook_helper.updates import REPO, SETUP_NAME, UpdateChecker, latest_installer


def release(tag="v99.0.0", url=None):
    return {
        "tag_name": tag,
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": SETUP_NAME,
                "state": "uploaded",
                "size": 1234,
                "browser_download_url": url
                or f"https://github.com/{REPO}/releases/download/{tag}/{SETUP_NAME}",
            }
        ],
    }


def test_version_comparison_and_installer_must_match_our_repo():
    assert latest_installer(release("v0.10.0"), current="0.9.0")["version"] == "0.10.0"
    assert latest_installer(release("v0.9.0"), current="0.10.0") is None
    assert latest_installer(release(url="https://example.com/malware.exe")) is None
    assert latest_installer({**release(), "prerelease": True}) is None
    with pytest.raises(ValueError):
        latest_installer(release("v99.0.0-rc1"))


def test_network_reply_is_nonblocking_and_daily_throttled(app, store):
    class Reply(QObject):
        finished = Signal()

        def error(self):
            return QNetworkReply.NetworkError.NoError

        def bytesAvailable(self):
            return 0

        def readAll(self):
            return QByteArray(json.dumps(release()).encode())

        def abort(self):
            self.finished.emit()

    reply = Reply()
    calls = []
    manager = SimpleNamespace(get=lambda request: (calls.append(request), reply)[1])
    checker = UpdateChecker(store, manager=manager)
    available = []
    checker.available.connect(available.append)
    checker.check(True)
    assert len(calls) == 1 and not available
    reply.finished.emit()
    assert available[0]["version"] == "99.0.0"
    checker.check(False)
    assert len(calls) == 1
    checker.stop()


def test_update_prompt_defers_during_posting_and_opens_only_accepted_installer(window, monkeypatch):
    from PySide6.QtGui import QDesktopServices

    info = latest_installer(release())
    prompts = []
    opened = []
    monkeypatch.setattr(window, "ask_update", lambda value: (prompts.append(value), True)[1])
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))
    window.queue_active = True
    window.update_available(info)
    assert not prompts and not opened
    window.queue_active = False
    window.offer_update()
    assert len(prompts) == 1 and opened == [info["url"]]
    window.update_available(info)
    assert len(prompts) == 1
