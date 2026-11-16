"""Exercise the actual Summernote library hosted in Qt WebEngine."""

from PySide6.QtCore import QMimeData

from facebook_helper.formatting import facebook_html


def paste(window, app, html):
    mime = QMimeData()
    mime.setHtml(html)
    mime.setText("Nội dung")
    app.clipboard().setMimeData(mime)
    window.content.paste()


def test_real_summernote_toolbar_is_loaded_offline(window):
    assert window.content.evaluate("$.summernote.version") == "0.9.1"
    assert window.content.evaluate("document.querySelectorAll('.note-toolbar button').length") > 12
    assert window.content.evaluate("!!document.querySelector('.note-icon-bold')")


def test_copy_facebook_dark_theme_removes_background_but_keeps_semantics(window, app):
    paste(
        window,
        app,
        '<div style="background-color:rgb(36,37,38);color:rgb(228,230,235);font-family:Times New Roman">'
        "<p><b>TUYỂN KỸ SƯ</b></p><p>Công việc <i>PLC</i></p><ul><li>Robot</li><li>HMI</li></ul></div>",
    )
    html = window.content.toHtml()
    assert "background" not in html and "228" not in html and "Times New Roman" not in html
    assert "<b>TUYỂN KỸ SƯ</b>" in html and "<i>PLC</i>" in html and "<ul>" in html
    assert "• Robot" in window.content.toPlainText()


def test_word_bold_color_size_survive_paste_save_and_reload(window, app, store):
    window.title.setText("Bài Word")
    paste(
        window, app, '<p><span style="font-weight:700;color:#2456ab;font-size:20pt">Nội dung đậm</span></p>'
    )
    before = window.content.toHtml()
    assert "font-weight" in before and "20pt" in before
    saved = store.post(window.save_post())
    window.content.clear()
    window.dirty = False
    window.load_post(window.post_list.item(0))
    assert window.content.toHtml() == saved["html"]
    assert "<b>" in facebook_html(saved["html"])


def test_library_bold_button_changes_selected_text(window):
    window.content.setPlainText("Tuyển kế toán")
    window.content.selectAll()
    window.content.evaluate("document.querySelector('.note-btn-bold').click()")
    assert "<b>" in window.content.toHtml()


def test_copy_mime_includes_html_plain_text_lists_and_hashtags(window, app):
    window.content.setHtml('<p><b>Tuyển dụng</b></p><ol start="3"><li>Kế toán</li><li>Kỹ sư</li></ol>')
    window.tags.setText("#HR")
    window.copy_editor()
    mime = app.clipboard().mimeData()
    assert mime.hasHtml() and mime.hasText()
    assert "<b>" in mime.html() and "#HR" in mime.html()
    assert "3. Kế toán" in mime.text() and "4. Kỹ sư" in mime.text()


def test_scripts_and_remote_images_are_not_loaded(window, app):
    messages = []
    window.content.notice = messages.append
    paste(
        window,
        app,
        '<p><b>Giữ chữ</b></p><img src="https://example.com/tracker.png"><script>window.bad=1</script>',
    )
    assert "script" not in window.content.toHtml() and "<img" not in window.content.toHtml()
    assert window.content.evaluate("window.bad||0") == 0
    assert messages and "Thêm ảnh" in messages[-1]


def test_plain_paste_does_not_take_source_html(window, app):
    mime = QMimeData()
    mime.setHtml("<b>Nguồn đậm</b>")
    mime.setText("Nguồn đậm")
    app.clipboard().setMimeData(mime)
    window.content.paste_plain()
    assert window.content.toPlainText() == "Nguồn đậm"
    assert "<b>" not in window.content.toHtml()


def test_native_library_lists_and_table_export_readably(window):
    window.content.setHtml(
        "<table><tr><td>Vị trí</td><td>Lương</td></tr><tr><td>Kỹ sư</td><td>20 triệu</td></tr></table>"
    )
    assert "Vị trí | Lương" in window.content.toPlainText()
    window.content.setPlainText("PLC\nRobot")
    window.content.selectAll()
    window.content.evaluate("editorApi.command('insertUnorderedList')")
    assert "• PLC" in window.content.toPlainText()


def test_semantic_facebook_html_converts_styles_and_drops_display_theme():
    html = facebook_html(
        '<p style="color:white;background-color:black"><span style="font-weight:700;font-style:italic">Kỹ sư</span></p><ul><li>PLC</li></ul>'
    )
    assert "<b><i>Kỹ sư</i></b>" in html
    assert "style=" not in html and "<ul>" in html


def test_loading_and_editing_different_posts_does_not_race(window):
    window.content.setHtml("<p><b>Bài thứ nhất</b></p>")
    window.content.setHtml("<p><i>Bài thứ hai</i></p>")
    assert window.content.toHtml() == "<p><i>Bài thứ hai</i></p>"
    assert window.content.toPlainText() == "Bài thứ hai"


def test_previous_qt_dark_draft_is_repaired_without_losing_bold(window):
    window.content.setHtml(
        '<html><head><meta name="qrichtext" content="1"></head><body><p style="background-color:#242526;color:#e4e6eb"><b>Bài cũ</b></p></body></html>'
    )
    html = window.content.toHtml()
    assert "background-color" not in html and "color" not in html
    assert "<b>Bài cũ</b>" in html


def test_user_chosen_highlight_survives_save_snapshot(window):
    window.content.setHtml(
        '<p><span style="background-color:rgb(10,20,180);color:rgb(255,255,255)">Tô màu có chủ ý</span></p>'
    )
    assert "background-color" in window.content.toHtml()
