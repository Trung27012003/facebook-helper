"""Validation shared by storage, browser automation and UI."""

import re
import unicodedata
from urllib.parse import parse_qs, urlparse

STATUSES = {
    "draft": "Chưa chuẩn bị",
    "prepared": "Đã chuẩn bị · chưa xác nhận đăng",
    "pending": "Chờ duyệt",
    "published": "Đã hiển thị (bạn xác nhận)",
    "rejected": "Bị từ chối",
    "error": "Có lỗi",
    "sending": "Đang gửi · chưa có kết quả",
    "submitted": "Đã gửi · cần kiểm tra",
    "uncertain": "Chưa rõ kết quả · kiểm tra Facebook",
    "skipped": "Đã bỏ qua",
}


def group_key(url: str) -> str:
    parsed = urlparse(url.strip())
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"}
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Hãy nhập link HTTPS của nhóm Facebook.")
    match = re.fullmatch(r"/groups/([A-Za-z0-9._-]+)(?:/(?:posts|permalink)/(\d+))?/?", parsed.path)
    if not match or match[1].lower() in {"feed", "discover", "joins", "create"}:
        raise ValueError("Link cần có dạng https://www.facebook.com/groups/ten-nhom/")
    return match[1]


def normalize_group(url: str) -> str:
    return f"https://www.facebook.com/groups/{group_key(url)}/"


def post_url(url: str, group_url: str) -> str:
    """Only accept identifiable post permalinks for the selected group."""
    if group_key(url) != group_key(group_url):
        raise ValueError("Link bài đăng phải thuộc nhóm đang chọn (cùng ID hoặc tên nhóm).")
    parsed = urlparse(url.strip())
    query = parse_qs(parsed.query)
    match = re.fullmatch(r"/groups/([^/]+)/(posts|permalink)/(\d+)/?", parsed.path)
    if match:
        return f"https://www.facebook.com/groups/{match[1]}/posts/{match[3]}/"
    ids = query.get("multi_permalinks", [])
    if len(ids) == 1 and ids[0].isdigit():
        return f"https://www.facebook.com/groups/{group_key(url)}/posts/{ids[0]}/"
    raise ValueError("Cần link của một bài cụ thể, không phải trang chủ nhóm.")


def excel_text(value):
    """Prevent spreadsheet formula execution from user-controlled text."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def parse_tags(value):
    """Comma/semicolon-separated labels; spaces within a label are significant."""
    result = {}
    for part in re.split(r"[,;\n]+", value):
        label = unicodedata.normalize("NFC", part.strip().lstrip("#").strip())
        if label:
            result.setdefault(label.casefold(), label)
    return list(result.values())
