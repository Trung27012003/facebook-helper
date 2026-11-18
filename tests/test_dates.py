from PySide6.QtCore import QDate, QLocale
from PySide6.QtTest import QTest


def test_entire_date_field_opens_vietnamese_calendar_and_selects_day(window, app):
    picker = window.post_manager.start
    window.tabs.setCurrentIndex(4)
    picker.click()
    app.processEvents()
    assert picker.popup.isVisible()
    assert picker.calendar.locale().language() == QLocale.Language.Vietnamese
    date = QDate.currentDate().addDays(-2)
    picker.calendar.clicked.emit(date)
    assert picker.date() == date and not picker.popup.isVisible()
    assert picker.text().startswith(date.toString("dd/MM/yyyy"))


def test_picker_text_fits_and_invalid_date_cannot_be_set(window, app):
    import pytest

    picker = window.post_manager.end
    window.resize(980, 680)
    window.tabs.setCurrentIndex(4)
    app.processEvents()
    assert picker.fontMetrics().horizontalAdvance(picker.text()) + 24 <= picker.width()
    before = picker.date()
    with pytest.raises(ValueError):
        picker.setDate(QDate())
    assert picker.date() == before
    picker.click()
    QTest.qWait(10)
    assert picker.popup.frameGeometry().right() <= picker.screen().availableGeometry().right()
