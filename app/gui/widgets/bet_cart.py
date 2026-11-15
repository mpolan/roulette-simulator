"""Koszyk utrzymujący obiekty i wiersze niezależnie od równości Bet."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem


class BetCart(QListWidget):
    remove_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = {}
        self.setAccessibleName("Koszyk zakładów. Delete usuwa zaznaczony zakład.")
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setToolTip("Dwuklik lub Delete: usuń jedną pozycję i zwróć jej stawkę.")
        self.itemDoubleClicked.connect(self._remove_item)

    def set_bets(self, bets):
        active_ids = {id(bet) for bet in bets}
        for identity in tuple(self.rows):
            if identity not in active_ids:
                item = self.rows.pop(identity)
                self.takeItem(self.row(item))
        for bet in bets:
            if id(bet) not in self.rows:
                selection = f" {bet.selection}" if bet.selection is not None else ""
                item = QListWidgetItem(f"{bet.bet_type.name}{selection}   ·   {bet.amount}$")
                item.setData(Qt.ItemDataRole.UserRole, bet)
                self.addItem(item)
                self.rows[id(bet)] = item
        if bets and self.currentItem() is None:
            self.setCurrentRow(0)

    def _remove_item(self, item):
        if self.isEnabled() and item is not None:
            self.remove_requested.emit(item.data(Qt.ItemDataRole.UserRole))

    def remove_current(self):
        self._remove_item(self.currentItem())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_current()
            event.accept()
            return
        super().keyPressEvent(event)
