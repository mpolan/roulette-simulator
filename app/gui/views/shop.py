"""Prezentacja katalogu oraz kolekcji Prestige Shop."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from gui.widgets.badge_card import BadgeCard


def _label(text="", role=None):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        label.setProperty("role", role)
    return label


class ShopView(QWidget):
    refresh_requested = Signal()
    buy_requested = Signal(str)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("shopView")
        self.setStyleSheet("""
            QWidget#shopView, QWidget#shopBody { background: #080D14; }
            QScrollArea { border: none; background: #080D14; }
            QFrame#badgeCard { background: #121D27; border: 1px solid #34424E; border-radius: 8px; }
            QLabel#badgeSymbol { background: #243442; color: #F5D58C; border: 1px solid #A58B58;
                                 border-radius: 19px; font-size: 22px; font-weight: 700; }
            QLabel#badgeName { color: #F0EDE5; font-size: 16px; font-weight: 700; }
            QLabel#badgePrice { color: #F5D58C; font-size: 16px; font-weight: 700; }
            QLabel#badgeDescription, QLabel#badgeState { color: #AEBBBE; font-size: 12px; }
            QLabel#shopBalance { color: #F5D58C; font-size: 21px; font-weight: 700; }
            QPushButton { padding: 6px 12px; min-height: 22px; }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 8)
        outer.setSpacing(8)
        header = QHBoxLayout()
        header.addWidget(_label("PRESTIGE SHOP", "section"), 1)
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.setAccessibleName("Odśwież sklep")
        self.back_button = QPushButton("Powrót do menu")
        header.addWidget(self.refresh_button)
        header.addWidget(self.back_button)
        outer.addLayout(header)

        profile = QFrame()
        profile.setProperty("panel", True)
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(14, 9, 14, 9)
        player_column = QVBoxLayout()
        player_column.setSpacing(2)
        player_column.addWidget(_label("AKTYWNY PROFIL", "hint"))
        self.player_label = _label("—")
        self.player_label.setObjectName("playerLabel")
        self.player_label.setWordWrap(True)
        player_column.addWidget(self.player_label)
        profile_layout.addLayout(player_column, 1)
        balance_column = QVBoxLayout()
        balance_column.setSpacing(2)
        balance_column.addWidget(_label("DOSTĘPNE SALDO", "hint"))
        self.balance_label = _label("—")
        self.balance_label.setObjectName("shopBalance")
        balance_column.addWidget(self.balance_label)
        profile_layout.addLayout(balance_column)
        outer.addWidget(profile)

        hint = _label("Odznaki są kosmetyczne. Nie zmieniają szans wygranej ani zasad ruletki.", "hint")
        hint.setWordWrap(True)
        outer.addWidget(hint)
        self.reason_label = _label("", "error")
        self.reason_label.setWordWrap(True)
        self.reason_label.hide()
        outer.addWidget(self.reason_label)
        self.message = _label()
        self.message.setWordWrap(True)
        self.message.hide()
        outer.addWidget(self.message)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("shopBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 4, 0)
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(8)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        body_layout.addLayout(self.grid)
        body_layout.addStretch()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)

        self.cards = {}
        self._owned_ids = set()
        self._balance = 0
        self._loaded = False
        self._purchase_blocked = True
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.back_button.clicked.connect(self.back_requested)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.back_requested)

    def set_player(self, name, balance):
        self.player_label.setText(name)
        self.balance_label.setText(f"{balance}$")
        self._balance = balance
        self._update_cards()

    def set_data(self, catalog, owned_badges):
        ids = [badge.id for badge in catalog]
        if list(self.cards) != ids:
            for card in self.cards.values():
                self.grid.removeWidget(card)
            for badge_id in list(self.cards):
                if badge_id not in ids:
                    self.cards.pop(badge_id).deleteLater()
            for index, badge in enumerate(catalog):
                if badge.id not in self.cards:
                    card = BadgeCard(badge)
                    card.buy_requested.connect(self._request_purchase)
                    self.cards[badge.id] = card
                self.grid.addWidget(self.cards[badge.id], index // 2, index % 2)
            self.cards = {badge.id: self.cards[badge.id] for badge in catalog}
        for badge in catalog:
            self.cards[badge.id].set_badge(badge)
        self._owned_ids = {badge.id for badge in owned_badges}
        self._loaded = True
        self.show_message("")
        self._update_cards()

    def set_state(self, navigation_blocked, purchase_blocked, reason=""):
        self.refresh_button.setEnabled(not navigation_blocked)
        self.back_button.setEnabled(not navigation_blocked)
        self._purchase_blocked = purchase_blocked
        self.reason_label.setText(reason if purchase_blocked else "")
        self.reason_label.setVisible(bool(self.reason_label.text()))
        self._update_cards()

    def show_message(self, text, error=False):
        self.message.setStyleSheet("color: #FF8E9B;" if error else "color: #72F5BA;")
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def invalidate_collection(self):
        self._loaded = False
        self._update_cards()

    def mark_purchased(self, purchase):
        self._owned_ids.add(purchase.badge_id)
        card = self.cards.get(purchase.badge_id)
        self.show_message(f"Kupiono {card.badge.name}." if card is not None else "Zakupiono odznakę.")
        self._update_cards()

    def reset(self):
        self.player_label.setText("—")
        self.balance_label.setText("—")
        self._balance = 0
        self._owned_ids.clear()
        self._loaded = False
        self.show_message("")
        self.reason_label.clear()
        self.reason_label.hide()
        self._update_cards()

    def _update_cards(self):
        for card in self.cards.values():
            card.set_state(card.badge.id in self._owned_ids, self._balance,
                           self._purchase_blocked or not self._loaded)

    def _request_purchase(self, badge_id):
        card = self.cards.get(badge_id)
        if card is not None and card.buy_button.isEnabled():
            self.buy_requested.emit(badge_id)
