"""Qt host for the unmodified, vendored Summernote library."""

import json
from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget


class EditorBridge(QObject):
    changed_signal = Signal(str, str, bool)
    loaded_signal = Signal()
    notice_signal = Signal(str)

    @Slot(str, str, bool)
    def changed(self, html, plain, user):
        self.changed_signal.emit(html, plain, user)

    @Slot()
    def loaded(self):
        self.loaded_signal.emit()

    @Slot(str)
    def notice(self, message):
        self.notice_signal.emit(message)


class SummernoteEditor(QWidget):
    textChanged = Signal()
    ready = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWebEngineView(self)
        self.profile = QWebEngineProfile(self)
        self.view.setPage(QWebEnginePage(self.profile, self.view))
        self._released = False
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        self.channel = QWebChannel(self.view.page())
        self.bridge = EditorBridge(self)
        self.channel.registerObject("editorBridge", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.bridge.changed_signal.connect(self._changed)
        self.bridge.loaded_signal.connect(self._loaded)
        self.bridge.notice_signal.connect(lambda message: self.notice(message) if self.notice else None)
        self._is_ready = False
        self._html = ""
        self._plain = ""
        self._placeholder = ""
        self.notice = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setMinimumHeight(230)
        self.view.load(QUrl.fromLocalFile(str(Path(__file__).parent / "assets" / "editor.html")))

    def _loaded(self):
        self._is_ready = True
        self.view.page().runJavaScript("editorApi.setContent(" + json.dumps(self._html) + ")")
        self.view.page().runJavaScript("editorApi.placeholder(" + json.dumps(self._placeholder) + ")")
        self.ready.emit()

    def _changed(self, html, plain, user):
        self._html, self._plain = html, plain
        if user:
            self.textChanged.emit()

    def wait_ready(self):
        if self._is_ready:
            return
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        self.ready.connect(loop.quit)
        timer.start(15000)
        loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        self.ready.disconnect(loop.quit)
        if not self._is_ready:
            raise RuntimeError(
                "Chưa tải được Summernote. Hãy kiểm tra thư mục _internal và giải nén lại toàn bộ ứng dụng."
            )

    def evaluate(self, script):
        self.wait_ready()
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        result = []

        def done(value):
            result.append(value)
            loop.quit()

        timer.timeout.connect(loop.quit)
        timer.start(5000)
        self.view.page().runJavaScript("JSON.stringify((" + script.rstrip("; ") + "))", done)
        if not result:
            loop.exec(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        if not result:
            raise RuntimeError("Trình soạn thảo chưa phản hồi. Nội dung chưa được lưu, vui lòng thử lại.")
        return json.loads(result[0]) if result[0] else None

    def _pull(self):
        data = self.evaluate("editorApi.snapshot()")
        if not isinstance(data, dict):
            raise RuntimeError("Summernote chưa khởi tạo xong. Vui lòng thử lại.")
        self._html, self._plain = data["html"], data["plain"]

    def toHtml(self):
        self._pull()
        return self._html

    def toPlainText(self):
        self._pull()
        return self._plain

    def setHtml(self, html):
        changed = html != self._html
        self._html = html
        if self._is_ready:
            self.view.page().runJavaScript("editorApi.setContent(" + json.dumps(html) + ")")
        if changed:
            self.textChanged.emit()

    def setPlainText(self, text):
        from html import escape

        self.setHtml("<p>" + escape(text).replace("\n", "<br>") + "</p>")

    def clear(self):
        self.setHtml("<p><br></p>")

    def setPlaceholderText(self, text):
        self._placeholder = text
        if self._is_ready:
            self.view.page().runJavaScript("editorApi.placeholder(" + json.dumps(text) + ")")

    def selectAll(self):
        self.evaluate("""(()=>{const el=document.querySelector('.note-editable');el.focus();
        const range=document.createRange();range.selectNodeContents(el);
        const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
        $('#editor').summernote('saveRange');return true;})()""")

    def paste(self):
        source = QApplication.clipboard().mimeData()
        self.evaluate(
            "editorApi.paste("
            + json.dumps(source.html() if source.hasHtml() else "")
            + ","
            + json.dumps(source.text())
            + ")"
        )

    def paste_plain(self):
        self.evaluate("editorApi.paste(''," + json.dumps(QApplication.clipboard().text()) + ",true)")

    def copy_article(self, tags=""):
        from PySide6.QtCore import QMimeData

        from .formatting import article_html

        html, text = self.toHtml(), self.toPlainText()
        mime = QMimeData()
        mime.setHtml(article_html(html, tags))
        mime.setText(text + ("\n\n" + tags.strip() if tags.strip() else ""))
        QApplication.clipboard().setMimeData(mime)

    def release(self):
        if not self._released:
            self._released = True
            self.view.stop()
            self.view.page().setWebChannel(None)
            self.view.page().deleteLater()
            self.view.deleteLater()
            self.profile.deleteLater()
