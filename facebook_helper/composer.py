"""Composer readiness checks. No body comparison, length check, or formatting gate."""

import time
import unicodedata

CONTENT_TIMEOUT = 12.0
UPLOAD_TIMEOUT = 90.0


def has_text(value):
    return bool("".join(char for char in value if unicodedata.category(char) != "Cf").strip())


EDITOR_TEXT = r"""el => {
 function text(node) {
  if(node.nodeType===3)return node.textContent;
  if(node.nodeType!==1)return '';
  if(node!==el && (node.getAttribute('contenteditable')==='false'||
    node.getAttribute('aria-hidden')==='true'||['button','status','alert'].includes(node.getAttribute('role'))||
    node.hasAttribute('data-lexical-placeholder')))return '';
  if(node.nodeType===1&&['IMG','SVG'].includes(node.tagName))return '';
  if(node!==el){const s=getComputedStyle(node);if(s.display==='none'||s.visibility==='hidden')return '';}
  return Array.from(node.childNodes).map(text).join('');
 }
 return text(el);
}"""


def wait_for_editor_content(page, dialog):
    """Only wait for Facebook to receive text. Never compare it with the saved article."""
    deadline = time.monotonic() + CONTENT_TIMEOUT
    while time.monotonic() < deadline:
        for editor in dialog.locator('[role="textbox"][contenteditable="true"]').all():
            try:
                if editor.is_visible() and has_text(editor.evaluate(EDITOR_TEXT)):
                    return
            except Exception:
                continue
        page.wait_for_timeout(100)
    raise ValueError("Facebook chưa nhận được phần chữ. Đã dừng để tránh đăng bài trống; không tự dán lại.")


def wait_for_uploads(page, dialog, check_notice=None):
    """Wait for explicit photo-upload progress, with a finite deadline."""
    deadline = time.monotonic() + UPLOAD_TIMEOUT
    idle_reads = 0
    while time.monotonic() < deadline:
        if check_notice:
            check_notice()
        busy = False
        for progress in dialog.locator('[role="progressbar"], progress, [data-uploading="true"]').all():
            try:
                if progress.is_visible():
                    complete = progress.evaluate("""el=>{
                      if(el.tagName==='PROGRESS')return el.value>=el.max;
                      const value=el.getAttribute('aria-valuenow'),max=el.getAttribute('aria-valuemax');
                      return value!==null&&max!==null&&Number(value)>=Number(max);
                    }""")
                    if not complete:
                        busy = True
                        break
            except Exception:
                busy = True
        if busy:
            idle_reads = 0
        else:
            idle_reads += 1
            if idle_reads >= 3:
                return
        page.wait_for_timeout(200)
    raise ValueError(
        "Ảnh vẫn đang tải lên Facebook. Đã dừng, chưa bấm Đăng; kiểm tra kết nối và ảnh trong Facebook."
    )
