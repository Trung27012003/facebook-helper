"""Validate the actual editable text, allowing equivalent browser rendering."""

import re
import time
import unicodedata

SETTLE_TIMEOUT = 8.0


def canonical_text(text):
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    text = unicodedata.normalize("NFC", text).casefold()
    text = text.replace("\u2028", "\n").replace("\u2029", "\n").replace("\r", "\n")
    # Normalize markers on BOTH sides; keep digits inside salaries, dates and contacts.
    text = re.sub(r"(?m)^[\t \u00a0]*(?:[•●▪◦*-]|\d+[.)])[\t \u00a0]+", "", text)
    letters = re.sub(r"[\W_]+", "", text)
    return letters if letters else text.strip()


SNAPSHOT = r"""el => {
 function walk(node) {
  if(node.nodeType===3)return node.textContent;
  if(node.nodeType!==1)return '';
  if(node!==el) {
   if(node.getAttribute('contenteditable')==='false'||node.getAttribute('aria-hidden')==='true'||
      node.getAttribute('role')==='button'||node.hasAttribute('data-lexical-placeholder'))return '';
   const style=getComputedStyle(node);if(style.display==='none'||style.visibility==='hidden')return '';
  }
  if(node.tagName==='BR')return '\n';
  if(node.tagName==='IMG')return '';
  const value=Array.from(node.childNodes).map(walk).join('');
  return value+(/^(P|DIV|LI|H[1-6]|BLOCKQUOTE|TR)$/.test(node.tagName)?'\n':'');
 }
 const range=document.createRange();range.selectNodeContents(el);
 const nodes=[el,...el.querySelectorAll('*')];
 return {texts:[el.innerText,range.toString(),walk(el)],
 bold:nodes.some(n=>Number(getComputedStyle(n).fontWeight)>=600),
 italic:nodes.some(n=>getComputedStyle(n).fontStyle==='italic'),
 list:!!el.querySelector('ul,ol,[role=list]')};
}"""


def wait_for_composer(page, dialog, body, markup=None):
    """Read back repeatedly until content AND formatting have settled. Never paste again."""
    expected = canonical_text(body)
    required = {
        "bold": bool(markup and re.search(r"<(?:b|strong|h[1-3])[ >]", markup)),
        "italic": bool(markup and re.search(r"<(?:i|em)[ >]", markup)),
        "list": bool(markup and re.search(r"<(?:ul|ol)[ >]", markup)),
    }
    deadline = time.monotonic() + SETTLE_TIMEOUT
    streak = 0
    last_match = None
    longest = 0
    while time.monotonic() < deadline:
        matching = None
        last_match = None
        for editor in dialog.locator('[role="textbox"][contenteditable="true"]').all():
            try:
                if not editor.is_visible():
                    continue
                snapshot = editor.evaluate(SNAPSHOT)
            except Exception:
                continue  # Facebook can replace the textbox after attaching a photo.
            values = [canonical_text(value) for value in snapshot["texts"]]
            longest = max(longest, *(len(value) for value in values))
            if expected in values:
                last_match = snapshot
                if all(not needed or snapshot[key] for key, needed in required.items()):
                    matching = snapshot
                    break
        if matching:
            streak += 1
            if streak >= 2:
                return
        else:
            streak = 0
        page.wait_for_timeout(120)
    if last_match:
        raise ValueError(
            "Ô đăng Facebook không giữ đủ định dạng của bài. Đã dừng trước khi bấm Đăng; hãy kiểm tra định dạng trong Facebook."
        )
    raise ValueError(
        "Phần chữ trong ô Facebook chưa khớp bài đã lưu sau khi chờ cập nhật. "
        f"Bản lưu: {len(expected)} ký tự đối chiếu; đã đọc tối đa: {longest}. "
        "Đã dừng trước khi Đăng và giữ nguyên bản đang soạn để bạn kiểm tra; không tự dán lại."
    )
