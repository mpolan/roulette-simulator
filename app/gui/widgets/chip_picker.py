"""Trwały selektor nominałów udostępnianych przez Game."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


CHIP_COLORS = {5: "#E5DED0", 10: "#D96872", 25: "#70B9A0", 50: "#79A7D4", 100: "#B29BCF"}


class ChipButton(QPushButton):
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFixedSize(52, 52)
        # Ogólny QSS przycisków ustawia min-height i potrafi obniżyć minimum
        # nadane przez setFixedSize; krążek wymaga własnej pełnej geometrii.
        self.setStyleSheet("QPushButton { min-width: 52px; max-width: 52px; "
                           "min-height: 52px; max-height: 52px; padding: 0; border: none; }")
        self.setAccessibleName(f"Żeton {value} dolarów")
        self.setToolTip(f"Żeton {value}$")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(CHIP_COLORS.get(self.value, "#F5D58C"))
        if self.isEnabled() and self.underMouse():
            color = color.lighter(115)
        if not self.isEnabled():
            color.setAlpha(100)
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#F5D58C" if self.isChecked() else "#34424E"), 3))
        painter.drawEllipse(3, 3, 46, 46)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#17232D"), 2, Qt.PenStyle.DashLine))
        painter.drawEllipse(9, 9, 34, 34)
        painter.setPen(QColor("#080D14"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(15)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.value))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#F0EDE5"), 2, Qt.PenStyle.DashLine))
            painter.drawEllipse(1, 1, 50, 50)


class ChipPicker(QWidget):
    chip_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.setMinimumHeight(52)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch()

    def set_values(self, values):
        if tuple(self.buttons) == tuple(values):
            return
        for button in self.buttons.values():
            self._layout.removeWidget(button)
            button.deleteLater()
        self.buttons.clear()
        for index, value in enumerate(values):
            button = ChipButton(value, self)
            button.clicked.connect(lambda checked=False, v=value: self.chip_selected.emit(v))
            self.buttons[value] = button
            self._layout.insertWidget(index, button)

    def set_selected(self, value):
        for chip_value, button in self.buttons.items():
            checked = chip_value == value
            if button.isChecked() != checked:
                button.setChecked(checked)
