import json
from types import SimpleNamespace

import pytest

from facebook_helper.browser import BrowserWorker
from facebook_helper.postlinks import SubmissionLinks


@pytest.fixture
def worker(tmp_path):
    value = BrowserWorker(tmp_path)
    dialog = SimpleNamespace(count=lambda: 0)
    dialog.filter = lambda **kwargs: dialog
    value.waits = []
    value.page = SimpleNamespace(
        wait_for_timeout=value.waits.append,
        get_by_role=lambda *args, **kw: dialog,
        locator=lambda *args: None,
    )
    return value


def test_transient_pre_send_failure_has_three_total_attempts(worker, monkeypatch):
    calls = []

    def execute(action, payload):
        calls.append(action)
        if len(calls) < 3:
            raise TimeoutError("network timeout")
        return {"sent": True}

    monkeypatch.setattr(worker, "execute", execute)
    result = worker.execute_recovering("publish", {})
    assert len(calls) == 3 and result["sent"] and result["attempts"] == 3
    assert worker.waits == [1000, 2000]


@pytest.mark.parametrize(
    "message", ["Facebook yêu cầu đăng nhập", "Facebook đang báo: temporarily blocked", "Ảnh không tồn tại"]
)
def test_auth_restrictions_and_invalid_files_are_not_retried(worker, monkeypatch, message):
    calls = []

    def execute(*args):
        calls.append(1)
        raise ValueError(message)

    monkeypatch.setattr(worker, "execute", execute)
    with pytest.raises(ValueError):
        worker.execute_recovering("publish", {})
    assert len(calls) == 1


def test_unknown_after_click_never_causes_a_second_click(worker, monkeypatch):
    calls = []

    def execute(*args):
        calls.append(1)
        return {"uncertain": True, "sent": False, "submission_started": True}

    monkeypatch.setattr(worker, "execute", execute)
    result = worker.execute_recovering("publish", {})
    assert result["uncertain"] and len(calls) == 1


@pytest.mark.parametrize(
    "story,transient,expected", [(None, True, True), (None, False, False), ({"id": "created"}, True, False)]
)
def test_only_explicit_rejected_creation_can_be_retried(story, transient, expected):
    capture = SubmissionLinks(
        SimpleNamespace(url="about:blank"), {"group_url": "https://www.facebook.com/groups/123/"}
    )
    capture.responses = [
        SimpleNamespace(
            text=lambda: json.dumps(
                {"data": {"story_create": story}, "errors": [{"is_transient": transient}]}
            )
        )
    ]
    assert capture.transient_rejection() == expected
