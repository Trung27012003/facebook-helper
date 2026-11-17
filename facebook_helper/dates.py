"""Date selection using Qt's Vietnamese calendar, without segmented text input."""

from PySide6.QtCore import QDate, QLocale, Qt, Signal
from PySide6.QtWidgets import QCalendarWidget, QFrame, QPushButton, QVBoxLayout


class DatePicker(QPushButton):
    dateChanged = Signal(QDate)

    def __init__(self, date=None, parent=None):
        super().__init__(parent)
        self._date = date or QDate.currentDate()
        self.setMinimumWidth(148)
        self.setProperty("datePicker", True)
        self.setToolTip("Bấm để chọn ngày")
        self.popup = QFrame(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup.setObjectName("datePopup")
        self.popup.setStyleSheet(
            "QFrame#datePopup {background:white;border:1px solid #cbd5e1;border-radius:8px;}"
        )
        layout = QVBoxLayout(self.popup)
        self.calendar = QCalendarWidget()
        self.calendar.setLocale(QLocale("vi_VN"))
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setMinimumSize(320, 260)
        self.calendar.clicked.connect(self.choose)
        self.calendar.activated.connect(self.choose)
        layout.addWidget(self.calendar)
        today = QPushButton("Hôm nay")
        today.clicked.connect(lambda: self.choose(QDate.currentDate()))
        layout.addWidget(today)
        self.clicked.connect(self.show_calendar)
        self.setDate(self._date)

    def date(self):
        return QDate(self._date)

    def setDate(self, value):
        if not isinstance(value, QDate) or not value.isValid():
            raise ValueError("Ngày không hợp lệ")
        changed = self._date != value
        self._date = QDate(value)
        self.setText(value.toString("dd/MM/yyyy") + "  ▾")
        self.calendar.setSelectedDate(value)
        if changed:
            self.dateChanged.emit(self.date())

    def show_calendar(self):
        self.calendar.setSelectedDate(self._date)
        self.calendar.showSelectedDate()
        self.popup.adjustSize()
        position = self.mapToGlobal(self.rect().bottomLeft())
        bounds = self.screen().availableGeometry()
        position.setX(max(bounds.left(), min(position.x(), bounds.right() - self.popup.width() + 1)))
        if position.y() + self.popup.height() > bounds.bottom():
            position.setY(self.mapToGlobal(self.rect().topLeft()).y() - self.popup.height())
        position.setY(max(bounds.top(), min(position.y(), bounds.bottom() - self.popup.height() + 1)))
        self.popup.move(position)
        self.popup.show()
        self.calendar.setFocus()

    def choose(self, date):
        self.setDate(date)
        self.popup.hide()
