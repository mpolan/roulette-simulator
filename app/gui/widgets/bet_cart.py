"""Grupy prezentacji zachowujące tożsamość każdego oryginalnego Bet."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem


class BetCart(QListWidget):
    remove_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = {}
        self._groups = {}
        self._bets = {}
        self.setAccessibleName("Koszyk zakładów. Delete usuwa ostatni zakład zaznaczonej grupy.")
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setToolTip("Dwuklik lub Delete: usuń jeden ostatni zakład z grupy i zwróć jego stawkę.")
        self.itemDoubleClicked.connect(self._remove_item)

    def set_bets(self, bets):
        groups = {}
        for bet in bets:
            groups.setdefault((bet.bet_type, bet.selection), []).append(bet)
        for key in tuple(self._groups):
            if key not in groups:
                item = self._groups.pop(key)
                self.takeItem(self.row(item))
        self._bets = {key: tuple(group) for key, group in groups.items()}
        self.rows = {}
        for key, group in self._bets.items():
            kind, selection = key
            item = self._groups.get(key)
            if item is None:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, key)
                self.addItem(item)
                self._groups[key] = item
            label = kind.name + (f" {selection}" if selection is not None else "")
            text = f"{label} · zakładów: {len(group)} · {sum(bet.amount for bet in group)}$"
            if item.text() != text:
                item.setText(text)
            item.setToolTip(text + f"\nUsuń / Delete / dwuklik: usuwa jeden ostatni zakład tej grupy "
                            f"i zwraca jego stawkę {group[-1].amount}$.")
            for bet in group:
                self.rows[id(bet)] = item
        if bets and self.currentItem() is None:
            self.setCurrentRow(0)

    def _remove_item(self, item):
        if self.isEnabled() and item is not None:
            group = self._bets.get(item.data(Qt.ItemDataRole.UserRole), ())
            if group:
                self.remove_requested.emit(group[-1])

    def remove_current(self):
        self._remove_item(self.currentItem())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_current()
            event.accept()
            return
        super().keyPressEvent(event)
