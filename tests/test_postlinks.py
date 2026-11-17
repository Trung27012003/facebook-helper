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
