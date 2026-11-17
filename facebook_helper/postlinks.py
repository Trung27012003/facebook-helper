"""Read a permalink from the response to this browser's own submit operation.

This does not issue API calls or retain request credentials. Unknown response
shapes deliberately produce no link; the rendered post remains a fallback.
"""

import json
from urllib.parse import parse_qs, urlparse

from .domain import group_key, post_url
from .monitoring import normalized


def matching_submission(request, payload):
    parsed = urlparse(request.url)
    if (
        request.method != "POST"
        or parsed.hostname not in {"www.facebook.com", "facebook.com"}
        or parsed.path.rstrip("/") != "/api/graphql"
    ):
        return False
    fields = parse_qs(request.post_data or "")
    if fields.get("fb_api_req_friendly_name") != ["ComposerStoryCreateMutation"]:
        return False
    try:
        variables = json.loads(fields["variables"][0])
        data = variables["input"]
        body = payload.get("body", "")
        return (
            bool(body.strip())
            and normalized(data["message"]["text"]) == normalized(body)
            and str(data["audience"]["to_id"]) == group_key(payload["group_url"])
        )
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def response_link(text, group_url):
    if text.startswith("for (;;);"):
        text = text[len("for (;;);") :].lstrip()
    candidates = set()
    try:
        documents = [json.loads(text)]
    except ValueError:
        documents = []
        for line in text.splitlines():
            try:
                documents.append(json.loads(line))
            except ValueError:
                continue
    for document in documents:
        try:
            if document.get("errors"):
                continue
            story = document["data"]["story_create"]["story"]
            if not isinstance(story, dict):
                continue
            for field in ("url", "permalink_url"):
                if story.get(field):
                    candidates.add(post_url(story[field], group_url))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return candidates.pop() if len(candidates) == 1 else ""


class SubmissionLinks:
    def __init__(self, page, payload):
        self.page = page
        self.payload = payload
        self.responses = []

    def completed(self, request):
        try:
            if matching_submission(request, self.payload):
                response = request.response()
                if response and response.ok:
                    self.responses.append(response)
        except Exception:
            pass  # Link enrichment must not affect the submit operation.

    def __enter__(self):
        self.page.on("requestfinished", self.completed)
        return self

    def __exit__(self, *args):
        self.page.remove_listener("requestfinished", self.completed)

    def link(self):
        candidates = set()
        for response in self.responses:
            try:
                link = response_link(response.text(), self.payload["group_url"])
                if link:
                    candidates.add(link)
            except Exception:
                pass
        return candidates.pop() if len(candidates) == 1 else ""
