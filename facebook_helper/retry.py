"""Bounded recovery of a prepared draft; never reload after an attempted send."""

import re

MAX_ATTEMPTS = 3


def transient_error(error):
    text = str(error).casefold()
    if text.startswith("facebook đang báo:"):
        return False
    if re.search(
        r"checkpoint|xác thực|đăng nhập|login|hạn chế|bị chặn|blocked|quy định|không tồn tại|không hợp lệ|cùng nội dung",
        text,
    ):
        return False
    return isinstance(error, (TimeoutError, ConnectionError)) or bool(
        re.search(
            r"timeout|timed out|net::err_|network|kết nối|mạng|reload|tải lại|tải lên|chưa nhận|chưa thấy ô|chưa dán|nút đăng|target.*closed",
            text,
        )
    )
