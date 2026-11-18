"""Native, searchable checkbox pickers; no Ctrl/Shift needed."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from .domain import parse_tags


class CheckList(QListWidget):
    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item and event.button() == Qt.MouseButton.LeftButton:
            self.setCurrentItem(item)
            item.setCheckState(
                Qt.CheckState.Unchecked
                if item.checkState() == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )
            event.accept()
        else:
            super().mousePressEvent(event)


class CheckPicker(QPushButton):
    changed = Signal()

    def __init__(self, placeholder="Chọn…", parent=None, editable=False):
        super().__init__(parent)
        self.placeholder = placeholder
        self.options = []
        self.setMinimumWidth(170)
        self.popup = QFrame(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup.setStyleSheet("QFrame {background:white;}")
        layout = QVBoxLayout(self.popup)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm lựa chọn…")
        self.search.textChanged.connect(self.filter_items)
        layout.addWidget(self.search)
        self.list = CheckList()
        self.list.setMinimumSize(300, 180)
        self.list.itemChanged.connect(self.selection_changed)
        layout.addWidget(self.list)
        if editable:
            line = QHBoxLayout()
            self.new_label = QLineEdit()
            self.new_label.setPlaceholderText("Thêm nhãn mới…")
            add = QPushButton("Thêm")
            add.clicked.connect(self.add_labels)
            self.new_label.returnPressed.connect(self.add_labels)
            line.addWidget(self.new_label)
            line.addWidget(add)
            layout.addLayout(line)
        close = QPushButton("Xong")
        close.clicked.connect(self.popup.hide)
        layout.addWidget(close)
        self.clicked.connect(self.open_popup)
        self.update_caption()

    def checked_data(self):
        return [
            self.list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.CheckState.Checked
        ]

    def labels(self):
        selected = set(self.checked_data())
        return [label for key, label in self.options if key in selected]

    def currentText(self):
        return ", ".join(self.labels())

    def setCurrentText(self, text):
        self.set_checked([key for key, label in self.options if label.casefold() == text.casefold()])

    def set_items(self, options):
        before = self.checked_data()
        self.options = list(options)
        self.list.blockSignals(True)
        self.list.clear()
        for key, label in self.options:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if key in before else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.blockSignals(False)
        self.filter_items()
        self.update_caption()
        if before != self.checked_data():
            self.changed.emit()

    def set_checked(self, values):
        before = self.checked_data()
        values = set(values)
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setCheckState(
                Qt.CheckState.Checked
                if item.data(Qt.ItemDataRole.UserRole) in values
                else Qt.CheckState.Unchecked
            )
        self.list.blockSignals(False)
        self.update_caption()
        if before != self.checked_data():
            self.changed.emit()

    def clear(self):
        self.set_checked([])

    def update_caption(self):
        labels = self.labels()
        caption = (
            (labels[0] if len(labels) == 1 else f"{labels[0]} +{len(labels) - 1}")
            if labels
            else self.placeholder
        )
        if len(caption) > 35:
            caption = caption[:32] + "…"
        QPushButton.setText(self, caption)
        self.setToolTip("\n".join(labels) or self.placeholder)

    def selection_changed(self, *args):
        self.update_caption()
        self.changed.emit()

    def filter_items(self, *args):
        text = self.search.text().strip().casefold()
        for i in range(self.list.count()):
            self.list.item(i).setHidden(text not in self.list.item(i).text().casefold())

    def open_popup(self):
        self.search.clear()
        self.popup.adjustSize()
        point = self.mapToGlobal(self.rect().bottomLeft())
        bounds = self.screen().availableGeometry()
        point.setX(max(bounds.left(), min(point.x(), bounds.right() - self.popup.width() + 1)))
        point.setY(max(bounds.top(), min(point.y(), bounds.bottom() - self.popup.height() + 1)))
        self.popup.move(point)
        self.popup.show()
        self.search.setFocus()

    def add_labels(self):
        labels = parse_tags(self.new_label.text())
        options = dict(self.options)
        selected = self.checked_data()
        for label in labels:
            options.setdefault(label.casefold(), label)
            selected.append(label.casefold())
        self.set_items(list(options.items()))
        self.set_checked(selected)
        self.new_label.clear()


class TagPicker(CheckPicker):
    def __init__(self, parent=None):
        super().__init__("Chọn một hoặc nhiều nhãn", parent, editable=True)

    def setText(self, text):
        labels = parse_tags(text)
        options = dict(self.options)
        for label in labels:
            options.setdefault(label.casefold(), label)
        self.set_items(list(options.items()))
        self.set_checked([label.casefold() for label in labels])
