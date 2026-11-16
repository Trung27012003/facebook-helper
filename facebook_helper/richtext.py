"""Native rich text editing and clipboard import without embedded web resources."""

import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
    QTextTableFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .widgets import button, row

ALLOWED_TAGS = {
    "p",
    "div",
    "span",
    "b",
    "strong",
    "i",
    "em",
    "u",
    "s",
    "strike",
    "del",
    "sub",
    "sup",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "td",
    "th",
    "a",
    "font",
    "html",
    "body",
}
STYLE_PROPERTIES = {
    "color",
    "background",
    "background-color",
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "text-decoration",
    "text-align",
    "vertical-align",
    "white-space",
    "line-height",
    "text-indent",
    "margin",
    "margin-left",
    "margin-right",
    "margin-top",
    "margin-bottom",
    "padding",
    "padding-left",
    "padding-right",
    "padding-top",
    "padding-bottom",
    "border",
    "border-color",
    "border-width",
    "border-style",
    "border-collapse",
    "width",
    "height",
    "list-style-type",
    "-qt-list-indent",
    "-qt-block-indent",
    "-qt-paragraph-type",
}


def safe_style(value):
    result = []
    for item in value.split(";"):
        name, sep, content = item.partition(":")
        name, content = name.strip().lower(), content.strip()
        if (
            sep
            and name in STYLE_PROPERTIES
            and content
            and not re.search(r"url\s*\(|expression\s*\(|javascript\s*:|@import|[<>\\]", content, re.I)
        ):
            result.append(f"{name}:{content}")
    return ";".join(result)


def safe_link(url):
    url = url.strip()
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return url
    if parsed.scheme.lower() in {"mailto", "tel"} and parsed.path:
        return url
    return ""


class ClipboardHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked = []
        self.css = None
        self.has_images = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "iframe", "object", "svg", "head", "title"}:
            # Keep <style> in head: Word places useful class definitions there.
            if tag != "head":
                self.blocked.append(tag)
            return
        if self.blocked:
            return
        if tag == "style":
            self.css = []
            return
        if tag == "img":
            self.has_images = True
            return
        if tag not in ALLOWED_TAGS:
            return
        clean = []
        for key, value in attrs:
            value = value or ""
            if key == "style":
                value = safe_style(value)
            elif key == "href" and tag == "a":
                value = safe_link(value)
            elif key in {"class", "align", "dir", "face", "color"}:
                pass
            elif key in {
                "rowspan",
                "colspan",
                "border",
                "cellpadding",
                "cellspacing",
                "width",
                "height",
                "start",
                "size",
            }:
                value = value if re.fullmatch(r"[+\-]?\d+%?", value) else ""
            else:
                continue
            if value:
                clean.append(f' {key}="{escape(value, quote=True)}"')
        self.parts.append(f"<{tag}{''.join(clean)}>")

    def handle_endtag(self, tag):
        if self.blocked:
            if tag == self.blocked[-1]:
                self.blocked.pop()
            return
        if tag == "style" and self.css is not None:
            cleaned = []
            css = (
                re.sub(r"/\*.*?\*/", "", "".join(self.css), flags=re.S).replace("<!--", "").replace("-->", "")
            )
            for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
                if re.fullmatch(r"[\w.\s,#:>*+\-]+", selector) and (style := safe_style(body)):
                    cleaned.append(f"{selector}{{{style}}}")
            if cleaned:
                self.parts.append("<style>" + "".join(cleaned) + "</style>")
            self.css = None
            return
        if tag in ALLOWED_TAGS and tag not in {"br", "hr"}:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.blocked:
            return
        if self.css is not None:
            self.css.append(data)
        else:
            self.parts.append(escape(data))


def clean_clipboard_html(value):
    parser = ClipboardHTML()
    parser.feed(value)
    parser.close()
    html = re.sub(
        r"(</(?:p|div|h[1-6]|ul|ol|li|table|tr|blockquote)>)[\s]+(?=<)",
        r"\1",
        "".join(parser.parts),
        flags=re.I,
    )
    return html, parser.has_images


def block_text(block):
    text = block.text().replace("\u2028", "\n")
    text_list = block.textList()
    if text_list is None:
        return text
    fmt = text_list.format()
    index = text_list.itemNumber(block) + fmt.start()
    style = fmt.style()
    if style == QTextListFormat.Style.ListDecimal:
        marker = f"{index}."
    elif style in {QTextListFormat.Style.ListLowerAlpha, QTextListFormat.Style.ListUpperAlpha}:
        n, marker = index, ""
        while n:
            n, remainder = divmod(n - 1, 26)
            marker = chr(97 + remainder) + marker
        marker = (marker.upper() if style == QTextListFormat.Style.ListUpperAlpha else marker) + "."
    elif style in {QTextListFormat.Style.ListLowerRoman, QTextListFormat.Style.ListUpperRoman}:
        n, marker = index, ""
        for amount, symbol in [
            (1000, "M"),
            (900, "CM"),
            (500, "D"),
            (400, "CD"),
            (100, "C"),
            (90, "XC"),
            (50, "L"),
            (40, "XL"),
            (10, "X"),
            (9, "IX"),
            (5, "V"),
            (4, "IV"),
            (1, "I"),
        ]:
            count, n = divmod(n, amount)
            marker += symbol * count
        marker = (marker.lower() if style == QTextListFormat.Style.ListLowerRoman else marker) + "."
    else:
        marker = "•"
    return "  " * max(0, fmt.indent() - 1) + marker + " " + text


def document_plain_text(document):
    """Export list markers and table rows as readable Facebook text."""
    lines, tables = [], set()
    block = document.begin()
    while block.isValid():
        cursor = QTextCursor(block)
        table = cursor.currentTable()
        if table:
            key = table.firstPosition()
            if key not in tables:
                tables.add(key)
                for r in range(table.rows()):
                    cells = []
                    for c in range(table.columns()):
                        cell = table.cellAt(r, c)
                        if (cell.row(), cell.column()) != (r, c):
                            cells.append("")
                            continue
                        current, end = cell.firstCursorPosition().block(), cell.lastCursorPosition().block()
                        parts = []
                        while current.isValid() and current.position() <= end.position():
                            parts.append(block_text(current))
                            current = current.next()
                        cells.append(" / ".join(parts))
                    lines.append(" | ".join(cells))
        else:
            lines.append(block_text(block))
        block = block.next()
    return "\n".join(lines)


class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.notice = None

    def loadResource(self, resource_type, name):
        # Pasted images are attachments, never automatic remote or local file requests.
        return None

    def insertFromMimeData(self, source):
        if source.hasHtml():
            html, images = clean_clipboard_html(source.html())
            self.textCursor().insertHtml(html)
            if images and self.notice:
                self.notice("Đã dán nội dung và định dạng. Ảnh trong bài cần thêm bằng nút Thêm ảnh.")
        elif source.hasText():
            self.insertPlainText(source.text())
        elif source.hasImage() and self.notice:
            self.notice("Để đính kèm ảnh, bấm Thêm ảnh và chọn tệp trên máy.")

    def toPlainText(self):
        return document_plain_text(self.document())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_V and event.modifiers() == (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        ):
            self.paste_plain()
            return
        super().keyPressEvent(event)

    def clear(self):
        super().clear()
        self.setCurrentCharFormat(QTextCharFormat())

    def paste_plain(self):
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFont(self.document().defaultFont())
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setForeground(self.palette().text().color())
        cursor.insertText(QApplication.clipboard().text(), fmt)
        self.setTextCursor(cursor)
        self.setFocus()

    def copy_article(self, tags=""):
        suffix = f"<p>{escape(tags.strip())}</p>" if tags.strip() else ""
        html = self.toHtml()
        # Keep tags inside the body rather than after the HTML document.
        html = html.replace("</body>", suffix + "</body>")
        plain = self.toPlainText().strip() + ("\n\n" + tags.strip() if tags.strip() else "")
        mime = QMimeData()
        mime.setHtml(html)
        mime.setText(plain)
        QApplication.clipboard().setMimeData(mime)


class RichTextToolbar(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.style = QComboBox()
        self.style.addItems(["Chữ thường", "Tiêu đề lớn", "Tiêu đề vừa", "Tiêu đề nhỏ"])
        self.style.currentIndexChanged.connect(self.set_heading)
        self.bold = button("Đậm", self.set_bold)
        self.italic = button("Nghiêng", self.set_italic)
        self.underline = button("Gạch chân", self.set_underline)
        for item in (self.bold, self.italic, self.underline):
            item.setCheckable(True)
            item.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.family = QFontComboBox()
        self.family.setMaximumWidth(190)
        self.family.currentFontChanged.connect(self.set_family)
        self.size = QSpinBox()
        self.size.setRange(8, 96)
        self.size.setValue(12)
        self.size.setSuffix(" pt")
        self.size.valueChanged.connect(self.set_size)
        layout.addLayout(row(self.style, self.bold, self.italic, self.underline, self.family, self.size))
        self.alignment = QComboBox()
        self.alignment.addItems(["Căn trái", "Căn giữa", "Căn phải", "Căn đều"])
        self.alignment.currentIndexChanged.connect(self.set_alignment)
        layout.addLayout(
            row(
                button("Màu chữ", self.choose_color),
                button("Tô nền", self.choose_highlight),
                button("• Danh sách", lambda: self.make_list(False)),
                button("1. Đánh số", lambda: self.make_list(True)),
                self.alignment,
                button("Liên kết", self.insert_link),
                button("Bảng", self.insert_table),
            )
        )
        layout.addLayout(
            row(
                button("Dán giữ định dạng", editor.paste),
                button("Dán chữ thuần", editor.paste_plain),
                button("Xóa định dạng", self.clear_format),
                button("Hoàn tác", editor.undo),
                button("Làm lại", editor.redo),
            )
        )
        editor.currentCharFormatChanged.connect(self.sync)
        editor.cursorPositionChanged.connect(lambda: self.sync(editor.currentCharFormat()))
        self.sync(editor.currentCharFormat())

    def merge(self, fmt):
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def set_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.bold.isChecked() else QFont.Weight.Normal)
        self.merge(fmt)

    def set_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic.isChecked())
        self.merge(fmt)

    def set_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline.isChecked())
        self.merge(fmt)

    def set_family(self, font):
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self.merge(fmt)

    def set_size(self, value):
        fmt = QTextCharFormat()
        fmt.setFontPointSize(value)
        self.merge(fmt)

    def choose_color(self):
        color = QColorDialog.getColor(self.editor.textColor(), self, "Chọn màu chữ")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self.merge(fmt)

    def choose_highlight(self):
        color = QColorDialog.getColor(QColor("#fff59d"), self, "Chọn màu tô nền")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self.merge(fmt)

    def set_alignment(self, index):
        values = [
            Qt.AlignmentFlag.AlignLeft,
            Qt.AlignmentFlag.AlignHCenter,
            Qt.AlignmentFlag.AlignRight,
            Qt.AlignmentFlag.AlignJustify,
        ]
        self.editor.setAlignment(values[index])
        self.editor.setFocus()

    def set_heading(self, level):
        cursor = self.editor.textCursor()
        fmt = cursor.blockFormat()
        fmt.setHeadingLevel(level)
        cursor.mergeBlockFormat(fmt)
        original = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        char = QTextCharFormat()
        char.setFontPointSize([12, 22, 18, 15][level])
        char.setFontWeight(QFont.Weight.Bold if level else QFont.Weight.Normal)
        cursor.mergeCharFormat(char)
        self.editor.setTextCursor(original)
        self.editor.setFocus()

    def make_list(self, numbered):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.Style.ListDecimal if numbered else QTextListFormat.Style.ListDisc)
        fmt.setIndent(1)
        cursor.createList(fmt)
        cursor.endEditBlock()
        self.editor.setFocus()

    def clear_format(self):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        original = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        fmt = QTextCharFormat()
        fmt.setFont(self.editor.document().defaultFont())
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.setForeground(QColor("#17243a"))
        fmt.setBackground(QBrush(Qt.BrushStyle.NoBrush))
        fmt.setAnchor(False)
        fmt.setAnchorHref("")
        fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor.setCharFormat(fmt)
        block = self.editor.document().findBlock(start)
        while block.isValid() and block.position() < max(end, start + 1):
            if block.textList():
                block.textList().remove(block)
            QTextCursor(block).setBlockFormat(QTextBlockFormat())
            block = block.next()
        cursor.endEditBlock()
        self.editor.setTextCursor(original)
        self.editor.setFocus()

    def insert_link(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chèn liên kết")
        layout = QFormLayout(dialog)
        text = QLineEdit(self.editor.textCursor().selectedText())
        url = QLineEdit()
        url.setPlaceholderText("https://... hoặc mailto:...")
        layout.addRow("Chữ hiển thị", text)
        layout.addRow("Đường dẫn", url)
        actions = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(actions)

        def insert():
            href = safe_link(url.text())
            if not href or not text.text().strip():
                url.setPlaceholderText("Nhập link http/https/mailto/tel và chữ hiển thị")
                return
            self.editor.textCursor().insertHtml(
                f'<a href="{escape(href, quote=True)}">{escape(text.text())}</a>'
            )
            dialog.accept()

        actions.accepted.connect(insert)
        actions.rejected.connect(dialog.reject)
        dialog.exec()

    def insert_table(self):
        dimensions, ok = QInputDialog.getItem(
            self,
            "Chèn bảng",
            "Chọn số hàng × số cột:",
            ["2 × 2", "3 × 2", "3 × 3", "4 × 3", "5 × 2"],
            0,
            False,
        )
        if not ok:
            return
        rows, columns = [int(value.strip()) for value in dimensions.split("×")]
        fmt = QTextTableFormat()
        fmt.setBorder(1)
        fmt.setCellPadding(5)
        cursor = self.editor.textCursor()
        cursor.insertTable(rows, columns, fmt)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def sync(self, fmt):
        controls = [
            self.bold,
            self.italic,
            self.underline,
            self.family,
            self.size,
            self.style,
            self.alignment,
        ]
        for item in controls:
            item.blockSignals(True)
        self.bold.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        self.italic.setChecked(fmt.fontItalic())
        self.underline.setChecked(fmt.fontUnderline())
        self.family.setCurrentFont(fmt.font())
        points = fmt.fontPointSize() or self.editor.document().defaultFont().pointSizeF()
        self.size.setValue(round(points) if points > 0 else 12)
        block_fmt = self.editor.textCursor().blockFormat()
        self.style.setCurrentIndex(min(block_fmt.headingLevel(), 3))
        alignment = self.editor.alignment()
        index = (
            1
            if alignment & Qt.AlignmentFlag.AlignHCenter
            else 2
            if alignment & Qt.AlignmentFlag.AlignRight
            else 3
            if alignment & Qt.AlignmentFlag.AlignJustify
            else 0
        )
        self.alignment.setCurrentIndex(index)
        for item in controls:
            item.blockSignals(False)
