"""Read-only inspection. A missing post never implies rejection or removal."""

import re
import unicodedata
from datetime import datetime
from urllib.parse import urlparse

from .domain import group_key, normalize_group, post_url

UNKNOWN = "Chưa xác minh được. Không đổi trạng thái đã lưu."
PATTERNS = {
    "pending": r"chờ (?:quản trị viên )?(?:phê )?duyệt|pending(?: admin)? approval|awaiting approval",
    "rejected": r"bài viết (?:này )?(?:đã )?bị (?:từ chối|từ chối phê duyệt)|post (?:was |has been )?declined",
    "removed": r"bài viết (?:này )?(?:đã )?bị gỡ|post (?:was |has been )?removed",
    "published": r"đã (?:được )?(?:phê duyệt|đăng)|\bpublished\b|\bapproved\b",
}


def normalized(text):
    text = re.sub(r"(?m)^\s*(?:[•●▪·*-]|\d+[.)])\s+", "", text)
    return " ".join(unicodedata.normalize("NFC", text).split()).casefold()


def classify(text):
    if re.search(r"not (?:yet )?(?:approved|published)|\bunapproved\b|\bunpublished\b", text, re.I):
        return None
    exact = {
        "pending": "pending",
        "chờ duyệt": "pending",
        "declined": "rejected",
        "bị từ chối": "rejected",
        "removed": "removed",
        "bị gỡ": "removed",
    }
    simple = re.sub(r"[\s·(]*\d+\)?$", "", normalized(text)).strip()
    if simple in exact:
        return exact[simple]
    for status, pattern in PATTERNS.items():
        if re.search(pattern, text, re.I):
            return status
    return None


def inspect_page(page, payload, own_content=False):
    """Only inspect matched cards; never infer status from arbitrary page text."""
    body = normalized(payload["body"])
    if not body:
        return {"outcome": "unknown", "message": UNKNOWN}
    cards = []
    for card in page.get_by_role("article").all():
        if not card.is_visible() or card.locator('xpath=ancestor::*[@role="dialog"]').count():
            continue
        text = normalized(card.inner_text())
        first_line = next((normalized(line) for line in payload["body"].splitlines() if line.strip()), "")
        if first_line and first_line in text and body not in text:
            more = card.get_by_role("button", name=re.compile(r"^(Xem thêm|See more)$", re.I))
            if more.count() == 1 and more.is_visible():
                more.click(timeout=2000)
                text = normalized(card.inner_text())
        if body not in text:
            continue
        urls = set()
        for href in card.locator("a[href]").evaluate_all("nodes=>nodes.map(n=>n.href)"):
            try:
                urls.add(post_url(href, payload["group_url"]))
            except ValueError:
                pass
        if payload.get("url") and post_url(payload["url"], payload["group_url"]) not in urls:
            continue
        if not payload.get("url"):
            # Body alone cannot distinguish a prior identical recruitment post.
            if not own_content or not payload.get("sent_at"):
                continue
            sent = datetime.fromisoformat(payload["sent_at"]).timestamp()
            times = []
            for node in card.locator("time[datetime], [data-utime]").all():
                try:
                    stamp = node.get_attribute("data-utime")
                    parsed = (
                        float(stamp)
                        if stamp
                        else datetime.fromisoformat(
                            node.get_attribute("datetime").replace("Z", "+00:00")
                        ).timestamp()
                    )
                    times.append(parsed)
                except (ValueError, TypeError, AttributeError):
                    pass
            if not any(abs(stamp - sent) <= 300 for stamp in times):
                continue
        cards.append((card, urls))
    if len(cards) != 1:
        return {
            "outcome": "unknown",
            "message": "Không nhận diện được duy nhất một bài đúng nội dung và link. " + UNKNOWN,
        }
    card, urls = cards[0]
    # Badges/alerts and selected category are metadata. Matching words inside the recruitment
    # body itself must never be mistaken for an approval notice.
    labels = card.locator('[role="status"], [role="alert"], [data-testid="post_status"]')
    status_text = " ".join(label.inner_text() for label in labels.all() if label.is_visible())
    if not status_text.strip():
        # Facebook often uses plain divs for status labels. Remove the entire matched
        # recruitment body and only accept complete UI labels, not words in comments.
        body_lines = {normalized(line) for line in payload["body"].splitlines()}
        label_pattern = re.compile(
            r"(?:(?:bài viết (?:này )?)?(?:đã )?(?:được )?(?:phê duyệt|bị từ chối|bị gỡ|đăng)|"
            r"(?:đang )?chờ (?:quản trị viên )?(?:phê )?duyệt|pending(?: admin)? approval|"
            r"(?:post (?:was |has been )?)?(?:approved|published|declined|removed)|"
            r"not (?:yet )?(?:approved|published)|unapproved|unpublished)",
            re.I,
        )
        status_text = "\n".join(
            line.strip()
            for line in card.inner_text().splitlines()
            if normalized(line) not in body_lines and label_pattern.fullmatch(line.strip())
        )
    selected_outcome = None
    card_outcome = classify(status_text)
    if own_content:
        selected = page.locator('[role="tab"][aria-selected="true"]')
        selected_outcome = next(
            (classify(x.inner_text()) for x in selected.all() if x.is_visible() and classify(x.inner_text())),
            None,
        )
        status_text += " " + " ".join(x.inner_text() for x in selected.all() if x.is_visible())
    if re.search(r"not (?:yet )?(?:approved|published)|\bunapproved\b|\bunpublished\b", status_text, re.I):
        return {"outcome": "unknown", "message": "Nhãn chưa đủ rõ để kết luận đã duyệt. " + UNKNOWN}
    if card_outcome and selected_outcome and card_outcome != selected_outcome:
        return {
            "outcome": "unknown",
            "message": "Nhãn bài và mục đang mở chưa khớp; trang có thể đang cập nhật. " + UNKNOWN,
        }
    outcome = card_outcome or selected_outcome
    if outcome and (own_content or payload.get("url")):
        if outcome == "published" and len(urls) != 1:
            return {
                "outcome": "unknown",
                "message": "Có dấu hiệu đã đăng nhưng chưa xác định được link duy nhất. " + UNKNOWN,
            }
        return {
            "outcome": outcome,
            "url": next(iter(urls)) if len(urls) == 1 else payload.get("url", ""),
            "message": "Đã đọc nhãn trạng thái của đúng bài: " + status_text.strip(),
        }
    # A known post found in the normal group discussion feed is observable publication,
    # whereas its permalink alone or the author's content manager can include pending drafts.
    is_feed = urlparse(page.url).path.rstrip("/") == urlparse(
        normalize_group(payload["group_url"])
    ).path.rstrip("/")
    if not own_content and is_feed and payload.get("url") and len(urls) == 1:
        if not re.search(PATTERNS["pending"], card.inner_text(), re.I):
            return {
                "outcome": "published",
                "url": next(iter(urls)),
                "message": "Đã tìm thấy đúng link và nội dung trong luồng thảo luận của nhóm.",
            }
    return {
        "outcome": "unknown",
        "message": "Tìm thấy bài nhưng chưa có bằng chứng về trạng thái duyệt. " + UNKNOWN,
    }


def check_post(page, payload):
    """Use a separate page, without clicking submit, moderation or destructive actions."""
    from .browser import check_platform_notice

    group_url = normalize_group(payload["group_url"])
    page.goto(group_url, wait_until="domcontentloaded")
    check_platform_notice(page, checking=True)
    if normalize_group(page.url) != group_url:
        raise ValueError("Chưa vào được đúng nhóm. Kiểm tra đăng nhập và quyền xem nhóm.")
    page.wait_for_timeout(1500)
    for _ in range(3):
        result = inspect_page(page, payload)
        if result["outcome"] != "unknown":
            return result
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(500)
    # Discover the user's own content link rather than hard-coding Facebook's private API.
    own_links = page.get_by_role(
        "link",
        name=re.compile(
            r"^(Quản lý bài viết|Quản lý bài viết của bạn|Nội dung của bạn|Bài viết của bạn|Manage your posts|Manage posts|Your content|Your posts)$",
            re.I,
        ),
    )
    candidates = set()
    for link in own_links.all():
        href = link.get_attribute("href")
        if not href:
            continue
        from urllib.parse import urljoin

        url = urljoin(page.url, href)
        try:
            # Explicit own-content paths exclude admin moderation queues and other groups.
            if group_key(group_url) == urlparse(url).path.split("/")[2] and urlparse(url).hostname in {
                "www.facebook.com",
                "facebook.com",
            }:
                if re.search(
                    r"/(your_content|my_content|my_pending_content|my_posted_content)(?:/|$)",
                    urlparse(url).path,
                ):
                    candidates.add(url)
        except (IndexError, ValueError):
            pass
    if len(candidates) == 1:
        own_url = candidates.pop()
        page.goto(own_url, wait_until="domcontentloaded")
        check_platform_notice(page, checking=True)
        if urlparse(page.url).path.rstrip("/") != urlparse(own_url).path.rstrip("/"):
            return {"outcome": "unknown", "message": "Facebook chuyển sang trang khác. " + UNKNOWN}
        page.wait_for_timeout(1000)
        for label in (
            None,
            r"^(Chờ duyệt|Pending|Đã đăng|Published|Bị từ chối|Declined|Bị gỡ|Removed)(?:\s*[·(]?\s*\d+\)?)?$",
        ):
            tabs = [None] if label is None else page.get_by_role("tab", name=re.compile(label, re.I)).all()
            for tab in tabs:
                if tab is not None:
                    tab.click()
                    page.wait_for_timeout(500)
                result = inspect_page(page, payload, own_content=True)
                if result["outcome"] != "unknown":
                    return result
    if payload.get("url"):
        page.goto(post_url(payload["url"], group_url), wait_until="domcontentloaded")
        check_platform_notice(page, checking=True)
        page.wait_for_timeout(1000)
        result = inspect_page(page, payload)
        if result["outcome"] != "unknown":
            return result
    return {"outcome": "unknown", "message": "Không tìm thấy bằng chứng duyệt trong phần đã tải. " + UNKNOWN}
