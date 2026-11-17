from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton


def button(text, callback, primary=False, danger=False):
    widget = QPushButton(text)
    widget.setProperty("primary", primary)
    widget.setProperty("danger", danger)
    widget.clicked.connect(callback)
    return widget


def row(*widgets):
    layout = QHBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def hint(text):
    label = QLabel(text)
    label.setObjectName("hint")
    label.setWordWrap(True)
    return label


def primary(widget, enabled):
    if widget.property("primary") != enabled:
        widget.setProperty("primary", enabled)
        widget.style().unpolish(widget)
        widget.style().polish(widget)


def menu_button(text):
    widget = button(text, lambda: None)
    widget.setMenu(QMenu(widget))
    return widget


def toolbar(*widgets):
    layout = row(*widgets)
    layout.addStretch()
    return layout
