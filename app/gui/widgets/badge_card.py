"""Karta katalogowej odznaki Prestige Shop."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


def _label(text=""):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label


class BadgeCard(QFrame):
    buy_requested = Signal(str)

    def __init__(self, badge, parent=None):
        super().__init__(parent)
        self.badge = badge
        self.setObjectName("badgeCard")
        self.setProperty("panel", True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(5)

        heading = QHBoxLayout()
        self.symbol_label = _label()
        self.symbol_label.setObjectName("badgeSymbol")
        self.symbol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.symbol_label.setFixedSize(38, 38)
        heading.addWidget(self.symbol_label)
        self.name_label = _label()
        self.name_label.setObjectName("badgeName")
        self.name_label.setWordWrap(True)
        heading.addWidget(self.name_label, 1)
        self.price_label = _label()
        self.price_label.setObjectName("badgePrice")
        heading.addWidget(self.price_label)
        layout.addLayout(heading)

        self.description_label = _label()
        self.description_label.setObjectName("badgeDescription")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label, 1)
        footer = QHBoxLayout()
        self.state_label = _label()
        self.state_label.setObjectName("badgeState")
        self.state_label.setWordWrap(True)
        footer.addWidget(self.state_label, 1)
        self.buy_button = QPushButton("Kup")
        self.buy_button.setAccessibleName(f"Kup odznakę {badge.name}")
        self.buy_button.clicked.connect(lambda: self.buy_requested.emit(self.badge.id))
        footer.addWidget(self.buy_button)
        layout.addLayout(footer)
        self._state = None
        self.set_badge(badge)

    def set_badge(self, badge):
        if self.badge != badge or not self.name_label.text():
            self.badge = badge
            self._state = None
            self.symbol_label.setText(badge.symbol)
            self.name_label.setText(badge.name)
            self.price_label.setText(f"{badge.price}$")
            self.description_label.setText(badge.description)
            self.buy_button.setAccessibleName(f"Kup odznakę {badge.name}")

    def set_state(self, owned, balance, blocked):
        state = (owned, balance, blocked)
        if state == self._state:
            return
        self._state = state
        self.buy_button.setEnabled(not owned and not blocked and balance >= self.badge.price)
        if owned:
            self.state_label.setText("POSIADANA")
            self.state_label.setStyleSheet("color: #72F5BA; font-weight: 600;")
            self.buy_button.setText("Posiadana")
        elif blocked:
            self.state_label.setText("Zakup niedostępny")
            self.state_label.setStyleSheet("")
            self.buy_button.setText("Kup")
        elif balance < self.badge.price:
            self.state_label.setText(f"Brakuje {self.badge.price - balance}$")
            self.state_label.setStyleSheet("")
            self.buy_button.setText("Brak środków")
        else:
            self.state_label.setText("Dostępna do zakupu")
            self.state_label.setStyleSheet("")
            self.buy_button.setText("Kup")
