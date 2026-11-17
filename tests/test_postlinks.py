import json
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from facebook_helper.domain import post_url
from facebook_helper.postlinks import matching_submission, response_link

GROUP = "https://www.facebook.com/groups/123/"
LINK = GROUP + "posts/pfbidABC123/"
BODY = "Tuyển dụng\nKỹ sư tự động hóa"


def request(
    body=BODY,
    group="123",
    name="ComposerStoryCreateMutation",
    url="https://www.facebook.com/api/graphql/",
    method="POST",
):
    return SimpleNamespace(
        url=url,
        method=method,
        post_data=urlencode(
            {
                "fb_api_req_friendly_name": name,
                "variables": json.dumps({"input": {"message": {"text": body}, "audience": {"to_id": group}}}),
            }
        ),
    )


def response(url=LINK, **extra):
    return json.dumps({"data": {"story_create": {"story": {"url": url}}}, **extra})


def test_capture_only_own_matching_submit():
    payload = {"group_url": GROUP, "body": BODY}
    assert matching_submission(request(), payload)
    for r in [
        request(body="Khác"),
        request(group="999"),
        request(name="CommentsCreateMutation"),
        request(method="GET"),
        request(url="https://example.com/api/graphql/"),
        request(url="https://www.facebook.com/api/other/"),
    ]:
        assert not matching_submission(r, payload)
    assert not matching_submission(request(), {**payload, "body": ""})


@pytest.mark.parametrize(
    "text",
    [
        "{",
        "null",
        "[]",
        '{"data": {"story_create": null}}',
        response(errors=[{"message": "Denied"}]),
        response(GROUP.replace("123", "999") + "posts/1/"),
        '{"data": {"story_create": {"story": {"id": "123"}}}}',
    ],
)
def test_unknown_error_or_unrelated_response_never_invents_link(text):
    assert response_link(text, GROUP) == ""


def test_supported_response_with_prefix_and_modern_permalink():
    assert response_link("for (;;);\n" + response(), GROUP) == LINK
    assert post_url(LINK + "?ref=test", GROUP) == LINK
    assert response_link(response() + "\n" + response(GROUP + "posts/999/"), GROUP) == ""


@pytest.mark.parametrize(
    "field,node", [("post_id", "story"), ("legacy_story_hideable_id", "story"), ("post_id", "root")]
)
def test_pending_response_with_post_id_but_no_url(field, node):
    created = {"story": {}}
    (created["story"] if node == "story" else created)[field] = "777"
    assert response_link(json.dumps({"data": {"story_create": created}}), GROUP) == GROUP + "posts/777/"


@pytest.mark.parametrize("value", [True, 0, {}, "Story:777", "999_777", "actor:123:777"])
def test_invalid_or_unrelated_typed_post_ids_are_not_used(value):
    text = json.dumps({"data": {"story_create": {"story": {"post_id": value}}}})
    assert response_link(text, GROUP) == ""


def test_conflicting_ids_or_foreign_url_never_fall_back():
    for story in [
        dict(post_id="777", legacy_story_hideable_id="888"),
        dict(url="https://www.facebook.com/groups/999/posts/777/", post_id="777"),
    ]:
        assert response_link(json.dumps({"data": {"story_create": {"story": story}}}), GROUP) == ""
    assert (
        response_link(json.dumps({"data": {"story_create": {"story": {"post_id": "123_777"}}}}), GROUP)
        == GROUP + "posts/777/"
    )


def test_alias_must_be_verified_before_accepting_numeric_destination():
    payload = {"group_url": "https://www.facebook.com/groups/jobs/", "body": BODY}
    assert not matching_submission(request(), payload)
    assert matching_submission(request(), {**payload, "target_group_id": "123"})
    assert not matching_submission(request(group="999"), {**payload, "target_group_id": "123"})
    assert not matching_submission(request(group=""), payload)
    assert response_link(response(), payload["group_url"]) == ""
    assert (
        response_link(response(), payload["group_url"], "123") == payload["group_url"] + "posts/pfbidABC123/"
    )


def test_wait_for_own_inflight_submission_without_approval():
    from facebook_helper.postlinks import SubmissionLinks

    capture = SubmissionLinks(SimpleNamespace(url="about:blank"), {"group_url": GROUP, "body": BODY})
    capture.pending.add("inflight")

    def tick(ms):
        capture.pending.clear()
        capture.responses.append(
            SimpleNamespace(
                text=lambda: json.dumps({"data": {"story_create": {"story": {"post_id": "777"}}}})
            )
        )

    capture.page.wait_for_timeout = tick
    assert capture.wait_for_link() == GROUP + "posts/777/"


def test_wait_for_link_is_bounded_and_does_not_repeat_submit(monkeypatch):
    import facebook_helper.postlinks as module
    from facebook_helper.postlinks import SubmissionLinks

    ticks = []
    page = SimpleNamespace(url="about:blank", wait_for_timeout=lambda ms: ticks.append(ms))
    capture = SubmissionLinks(page, {"group_url": GROUP, "body": BODY})
    capture.pending.add("inflight")
    now = iter([0, 0.1, 0.2, 0.4])
    monkeypatch.setattr(module.time, "monotonic", lambda: next(now))
    assert capture.wait_for_link(timeout_ms=300) == ""
    assert ticks == [100, 100]


def test_link_enrichment_does_not_fail_successful_submit_when_page_closes():
    from facebook_helper.postlinks import SubmissionLinks

    def closed(ms):
        raise RuntimeError("page closed")

    capture = SubmissionLinks(
        SimpleNamespace(url="about:blank", wait_for_timeout=closed), {"group_url": GROUP, "body": BODY}
    )
    capture.pending.add("inflight")
    assert capture.wait_for_link() == ""
