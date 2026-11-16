import pytest
from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor

from facebook_helper.richtext import clean_clipboard_html, safe_link


def format_at(editor, position=0):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
    return cursor.charFormat()


def paste_html(window, app, html, text="Nguồn có định dạng"):
    mime = QMimeData()
    mime.setHtml(html)
    mime.setText(text)
    app.clipboard().setMimeData(mime)
    window.content.paste()


def test_paste_word_html_keeps_font_bold_underline_color_and_size(window, app):
    paste_html(
        window,
        app,
        """<html><head><title>Không chèn tiêu đề tài liệu</title></head><body>
    <!--StartFragment--><p class="MsoNormal"><span style="font-family:Arial;font-size:18pt;
    font-weight:700;color:#c02030;background-color:#fff59d;text-decoration:underline">Tuyển kỹ sư</span></p>
    <p><i>Chào đón Fresher</i></p><!--EndFragment--></body></html>""",
    )
    assert window.content.toPlainText() == "Tuyển kỹ sư\nChào đón Fresher"
    fmt = format_at(window.content)
    assert fmt.fontWeight() == QFont.Weight.Bold
    assert fmt.fontUnderline() and fmt.fontPointSize() == 18
    assert fmt.foreground().color().name() == "#c02030"
    assert fmt.background().color().name() == "#fff59d"
    assert "Arial" in fmt.fontFamilies()
    assert window.dirty


def test_formatted_paste_survives_save_and_reload(window, store, app):
    window.title.setText("Bài dán từ Word")
    paste_html(
        window,
        app,
        '<p><b style="color:#2456ab">Nội dung đậm màu xanh</b></p><ul><li>PLC</li><li>Robot</li></ul>',
    )
    post = store.post(window.save_post())
    assert "• PLC" in post["plain"] and "• Robot" in post["plain"]
    window.content.clear()
    window.dirty = False
    window.load_post(window.post_list.item(0))
    assert format_at(window.content).fontWeight() == QFont.Weight.Bold
    assert format_at(window.content).foreground().color().name() == "#2456ab"
    assert "• PLC" in window.content.toPlainText()


def test_copy_full_article_contains_html_plain_text_and_tags(window, app):
    window.content.setHtml('<p><b>Vị trí tuyển dụng</b></p><ol start="3"><li>Kế toán</li><li>Kỹ sư</li></ol>')
    window.tags.setText("#TuyenDung")
    window.copy_editor()
    mime = app.clipboard().mimeData()
    assert mime.hasHtml() and mime.hasText()
    assert "font-weight:700" in mime.html()
    assert "3. Kế toán" in mime.text() and "4. Kỹ sư" in mime.text()
    assert mime.text().endswith("\n\n#TuyenDung")
    assert mime.html().index("#TuyenDung") < mime.html().index("</body>")


def test_paste_plain_does_not_import_source_format(window, app):
    mime = QMimeData()
    mime.setHtml('<b style="color:red">Đậm màu đỏ</b>')
    mime.setText("Đậm màu đỏ")
    app.clipboard().setMimeData(mime)
    window.content.paste_plain()
    assert window.content.toPlainText() == "Đậm màu đỏ"
    assert format_at(window.content).fontWeight() != QFont.Weight.Bold
    assert format_at(window.content).foreground().color().name() != "#ff0000"


def test_toolbar_tracks_format_at_cursor_without_changing_document(window):
    window.content.setHtml('<p><b><u style="font-size:20pt">Đậm</u></b> bình thường</p>')
    before = window.content.toHtml()
    cursor = QTextCursor(window.content.document())
    cursor.setPosition(1)
    window.content.setTextCursor(cursor)
    assert window.editor_toolbar.bold.isChecked() and window.editor_toolbar.underline.isChecked()
    assert window.editor_toolbar.size.value() == 20
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.content.setTextCursor(cursor)
    assert not window.editor_toolbar.bold.isChecked() and not window.editor_toolbar.underline.isChecked()
    assert window.content.toHtml() == before


def test_list_buttons_preserve_markers_for_facebook_plain_text(window):
    window.content.setPlainText("Kế toán\nKỹ sư")
    window.content.selectAll()
    window.editor_toolbar.make_list(False)
    assert window.content.toPlainText() == "• Kế toán\n• Kỹ sư"
    window.content.selectAll()
    window.editor_toolbar.make_list(True)
    assert window.content.toPlainText() == "1. Kế toán\n2. Kỹ sư"


def test_heading_alignment_and_clear_format_keep_text(window):
    window.content.setPlainText("QUYỀN LỢI")
    window.content.selectAll()
    window.editor_toolbar.set_heading(1)
    window.editor_toolbar.set_alignment(1)
    fmt = QTextCharFormat()
    fmt.setForeground(QColor("red"))
    fmt.setBackground(QColor("yellow"))
    fmt.setFontUnderline(True)
    window.content.mergeCurrentCharFormat(fmt)
    assert window.content.textCursor().blockFormat().headingLevel() == 1
    assert window.content.alignment() & Qt.AlignmentFlag.AlignHCenter
    window.content.selectAll()
    window.editor_toolbar.clear_format()
    assert window.content.toPlainText() == "QUYỀN LỢI"
    assert format_at(window.content).fontWeight() == QFont.Weight.Normal
    assert not format_at(window.content).fontUnderline()
    assert window.content.document().begin().blockFormat().headingLevel() == 0
    assert window.content.alignment() & Qt.AlignmentFlag.AlignLeft


def test_pasted_table_and_hyperlink_preserve_html_and_readable_text(window, app):
    paste_html(
        window,
        app,
        '<table border="1"><tr><td>Vị trí</td><td>Thu nhập</td></tr>'
        '<tr><td>Kỹ sư</td><td>20 triệu</td></tr></table><p><a href="https://example.com/jobs">Ứng tuyển</a></p>',
    )
    text = window.content.toPlainText()
    assert "Vị trí | Thu nhập" in text and "Kỹ sư | 20 triệu" in text
    assert "Ứng tuyển" in text
    assert 'href="https://example.com/jobs"' in window.content.toHtml()
    assert "<table" in window.content.toHtml()


def test_paste_strips_external_resources_and_scripts_but_keeps_styled_text(window, app):
    html = """<p><b>Giữ nội dung</b></p><script>không chèn mã này</script>
    <img src="file:///private/image.png"><img src="https://example.com/track.png">
    <span style="color:blue;background:url(file:///private/image.png)">Màu xanh</span>
    <a href="javascript:alert(1)">Liên hệ</a><iframe src="https://example.com">ẩn</iframe>"""
    clean, images = clean_clipboard_html(html)
    assert images and "src=" not in clean and "javascript" not in clean and "url(" not in clean
    assert "không chèn mã này" not in clean
    notices = []
    window.content.notice = notices.append
    paste_html(window, app, html)
    assert "Giữ nội dung" in window.content.toPlainText() and "Màu xanh" in window.content.toPlainText()
    assert notices and "Thêm ảnh" in notices[0]
    block = window.content.document().begin()
    while block.isValid():
        item = block.begin()
        while not item.atEnd():
            assert not item.fragment().charFormat().isImageFormat()
            item += 1
        block = block.next()


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,hi", "https://[invalid"]
)
def test_link_import_rejects_unsupported_or_malformed_urls(url):
    assert safe_link(url) == ""


def test_word_style_definitions_are_imported(window, app):
    paste_html(
        window,
        app,
        "<html><head><style><!-- /* Word style definitions */ p.HR {font-size:19pt;color:#123abc;font-weight:bold;} --></style></head>"
        '<body><p class="HR">Tin tuyển dụng</p></body></html>',
    )
    fmt = format_at(window.content)
    assert fmt.fontPointSize() == 19 and fmt.fontWeight() == QFont.Weight.Bold
    assert fmt.foreground().color().name() == "#123abc"


def test_keyboard_paste_and_plain_paste_shortcuts(window, app):
    from PySide6.QtTest import QTest

    mime = QMimeData()
    mime.setHtml("<b>Đậm từ clipboard</b>")
    mime.setText("Đậm từ clipboard")
    app.clipboard().setMimeData(mime)
    window.content.setFocus()
    QTest.keyClick(window.content, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    assert format_at(window.content).fontWeight() == QFont.Weight.Bold
    window.content.clear()
    QTest.keyClick(
        window.content, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    )
    assert window.content.toPlainText() == "Đậm từ clipboard"
    assert format_at(window.content).fontWeight() != QFont.Weight.Bold


def test_list_format_undo_redo_preserves_content(window):
    window.content.setPlainText("Công việc\nQuyền lợi")
    window.content.selectAll()
    window.editor_toolbar.make_list(False)
    assert window.content.toPlainText() == "• Công việc\n• Quyền lợi"
    window.content.undo()
    assert window.content.toPlainText() == "Công việc\nQuyền lợi"
    window.content.redo()
    assert window.content.toPlainText() == "• Công việc\n• Quyền lợi"


def test_toolbar_inserts_native_table(window, monkeypatch):
    from PySide6.QtWidgets import QInputDialog

    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: ("3 × 2", True))
    window.editor_toolbar.insert_table()
    table = window.content.textCursor().currentTable()
    assert table.rows() == 3 and table.columns() == 2
    table.cellAt(0, 0).firstCursorPosition().insertText("Vị trí")
    table.cellAt(0, 1).firstCursorPosition().insertText("Lương")
    assert "Vị trí | Lương" in window.content.toPlainText()
