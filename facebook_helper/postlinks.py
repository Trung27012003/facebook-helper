"""Read a permalink from the response to this browser's own submit operation.

This does not issue API calls or retain request credentials. Unknown response
shapes deliberately produce no link; the rendered post remains a fallback.
"""

import json
import re
import time
from urllib.parse import parse_qs, urlparse

from .domain import group_key, normalize_group, post_url
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
    friendly = fields.get(
        "fb_api_req_friendly_name", [getattr(request, "headers", {}).get("x-fb-friendly-name", "")]
    )
    if friendly != ["ComposerStoryCreateMutation"]:
        return False
    try:
        variables = json.loads(fields["variables"][0])
        data = variables["input"]
        body = payload.get("body", "")
        audience = str(data["audience"]["to_id"])
        return (
            bool(body.strip())
            and bool(audience)
            and normalized(data["message"]["text"]) == normalized(body)
            and audience in {group_key(payload["group_url"]), payload.get("target_group_id", "")}
        )
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def response_link(text, group_url, group_id=None):
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
                return ""
            created = document["data"]["story_create"]
            if created.get("errors"):
                return ""
            story = created.get("story") or {}
            if not isinstance(story, dict):
                continue
            urls = [story[field] for field in ("url", "permalink_url") if story.get(field)]
            if urls:
                # Explicit foreign/ambiguous URLs must never fall back to a guessed ID.
                validated = set()
                for url in urls:
                    if group_id and group_key(url) == group_id:
                        canonical = post_url(url, normalize_group(url))
                        identifier = urlparse(canonical).path.strip("/").split("/")[-1]
                        validated.add(
                            post_url(normalize_group(group_url) + "posts/" + identifier + "/", group_url)
                        )
                    else:
                        validated.add(post_url(url, group_url))
                candidates.update(validated)
            else:
                for node in (created, story):
                    for field in ("post_id", "legacy_story_hideable_id"):
                        value = node.get(field)
                        if isinstance(value, bool) or not isinstance(value, (str, int)):
                            continue
                        value = str(value)
                        compound = re.fullmatch(r"([1-9]\d*)_([1-9]\d*)", value)
                        if compound and compound[1] in {group_key(group_url), group_id}:
                            value = compound[2]
                        if re.fullmatch(r"[1-9]\d*|pfbid[A-Za-z0-9]+", value):
                            candidates.add(
                                post_url(normalize_group(group_url) + "posts/" + value + "/", group_url)
                            )
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return candidates.pop() if len(candidates) == 1 else ""


class SubmissionLinks:
    def __init__(self, page, payload):
        self.page = page
        self.payload = dict(payload)
        self.responses = []
        self.pending = set()
        # A named group can expose its numeric identity in its canonical metadata.
        # Only trust metadata from the exact group page already validated by the worker.
        try:
            if not group_key(payload["group_url"]).isdigit() and normalize_group(page.url) == normalize_group(
                payload["group_url"]
            ):
                identities = set()
                for node in page.locator('link[rel="canonical"],meta[property="og:url"]').all():
                    url = node.get_attribute("href") or node.get_attribute("content") or ""
                    if urlparse(url).path.rstrip("/") == "/groups/" + group_key(url):
                        key = group_key(url)
                        if key.isdigit():
                            identities.add(key)
                if len(identities) == 1:
                    self.payload["target_group_id"] = identities.pop()
        except Exception:
            pass

    def started(self, request):
        try:
            if matching_submission(request, self.payload):
                self.pending.add(request)
        except Exception:
            pass

    def failed(self, request):
        self.pending.discard(request)

    def completed(self, request):
        self.pending.discard(request)
        try:
            if matching_submission(request, self.payload):
                response = request.response()
                if response and response.ok:
                    self.responses.append(response)
        except Exception:
            pass  # Link enrichment must not affect the submit operation.

    def __enter__(self):
        self.page.on("request", self.started)
        self.page.on("requestfailed", self.failed)
        self.page.on("requestfinished", self.completed)
        return self

    def __exit__(self, *args):
        self.page.remove_listener("request", self.started)
        self.page.remove_listener("requestfailed", self.failed)
        self.page.remove_listener("requestfinished", self.completed)

    def wait_for_link(self, timeout_ms=3000):
        deadline = time.monotonic() + timeout_ms / 1000
        while self.pending and time.monotonic() < deadline:
            try:
                self.page.wait_for_timeout(100)
            except Exception:
                break  # Optional enrichment cannot turn an accepted send into a retry.
        return self.link()

    def link(self):
        candidates = set()
        for response in self.responses:
            try:
                link = response_link(
                    response.text(), self.payload["group_url"], self.payload.get("target_group_id")
                )
                if link:
                    candidates.add(link)
            except Exception:
                pass
        return candidates.pop() if len(candidates) == 1 else ""
