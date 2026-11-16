from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton


def button(text, callback, primary=False):
    widget = QPushButton(text)
    widget.setProperty("primary", primary)
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
