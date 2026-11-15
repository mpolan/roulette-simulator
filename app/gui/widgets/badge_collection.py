"""Prezentacja odznak zwróconych przez ShopService."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class BadgeCollection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.empty_label = QLabel("Kolekcja jest pusta. Odznaki znajdziesz w Prestige Shop.")
        self.empty_label.setProperty("role", "hint")
        self.empty_label.setWordWrap(True)
        self.list_widget = QListWidget()
        self.list_widget.setAccessibleName("Zakupione odznaki")
        self.list_widget.setMinimumHeight(76)
        self.list_widget.setMaximumHeight(140)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.list_widget)
        self.set_badges(())

    def set_badges(self, badges):
        badges = tuple(badges)
        for index, badge in enumerate(badges):
            text = f"{badge.symbol}   {badge.name}"
            item = self.list_widget.item(index)
            if item is None:
                item = QListWidgetItem()
                self.list_widget.addItem(item)
            if item.text() != text:
                item.setText(text)
            item.setData(Qt.ItemDataRole.UserRole, badge.id)
            item.setToolTip(badge.description)
        while self.list_widget.count() > len(badges):
            self.list_widget.takeItem(self.list_widget.count() - 1)
        row_height = self.list_widget.sizeHintForRow(0) if badges else 0
        self.list_widget.setFixedHeight(min(140, max(76, row_height * len(badges) + 2 * self.list_widget.frameWidth())))
        self.empty_label.setVisible(not badges)
        self.list_widget.setVisible(bool(badges))
