"""Prezentacja gotowych statystyk i zakupionej kolekcji gracza."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from gui.widgets.badge_collection import BadgeCollection


def _label(text="", role=None):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        label.setProperty("role", role)
    return label


class StatisticsView(QWidget):
    refresh_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statisticsView")
        self.setStyleSheet("""
            QWidget#statisticsView, QWidget#statisticsBody { background: #080D14; }
            QScrollArea { border: none; background: #080D14; }
            QFrame[metric="true"] { background: #121D27; border: 1px solid #34424E; border-radius: 8px; }
            QLabel[metricValue="true"] { color: #F5D58C; font-size: 20px; font-weight: 700; }
            QLabel[metricTitle="true"] { color: #AEBBBE; font-size: 12px; }
            QPushButton { padding: 6px 12px; min-height: 22px; }
            QListWidget::item { padding: 7px 10px; }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 8)
        outer.setSpacing(8)
        header = QHBoxLayout()
        title = _label("STATYSTYKI GRACZA", "section")
        title.setObjectName("statisticsTitle")
        header.addWidget(title, 1)
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.setAccessibleName("Odśwież statystyki")
        self.back_button = QPushButton("Powrót do menu")
        header.addWidget(self.refresh_button)
        header.addWidget(self.back_button)
        outer.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("statisticsBody")
        content = QVBoxLayout(body)
        content.setContentsMargins(0, 0, 4, 0)
        content.setSpacing(8)
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)

        profile = QFrame()
        profile.setProperty("panel", True)
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(14, 9, 14, 9)
        player_box = QVBoxLayout()
        player_box.setSpacing(2)
        player_box.addWidget(_label("AKTYWNY PROFIL", "hint"))
        self.player_label = _label("—")
        self.player_label.setObjectName("playerLabel")
        self.player_label.setWordWrap(True)
        player_box.addWidget(self.player_label)
        profile_layout.addLayout(player_box, 1)
        balance_box = QVBoxLayout()
        balance_box.setSpacing(2)
        balance_box.addWidget(_label("ZAPISANE SALDO", "hint"))
        self.balance_label = _label("—")
        self.balance_label.setProperty("metricValue", True)
        balance_box.addWidget(self.balance_label)
        profile_layout.addLayout(balance_box)
        content.addWidget(profile)

        self.no_rounds_label = _label("Brak rozegranych rund.", "hint")
        content.addWidget(self.no_rounds_label)
        self.values = {}
        self._section(content, "ROZGRYWKA", (
            ("total_rounds", "Rozegrane rundy"), ("profitable_rounds", "Rundy z zyskiem"),
            ("total_bets", "Wszystkie zakłady"), ("winning_bets", "Wygrane zakłady"),
        ))
        self._section(content, "FINANSE", (
            ("total_stake", "Łączne stawki"), ("total_payout", "Łączne wypłaty"),
            ("net_profit", "Bilans netto"), ("biggest_payout", "Największa wypłata z rundy"),
        ))
        self._section(content, "SKUTECZNOŚĆ", (
            ("win_rate", "Rundy z zyskiem"), ("bet_win_rate", "Wygrane zakłady"),
        ))

        collection_panel = QFrame()
        collection_panel.setProperty("panel", True)
        collection_layout = QVBoxLayout(collection_panel)
        collection_layout.setContentsMargins(14, 10, 14, 10)
        collection_layout.setSpacing(5)
        collection_header = QHBoxLayout()
        collection_header.addWidget(_label("KOLEKCJA ODZNAK", "section"), 1)
        self.badge_count_label = _label("Posiadane: —", "hint")
        self.spent_label = _label("Wydano w sklepie: —", "hint")
        collection_header.addWidget(self.badge_count_label)
        collection_header.addWidget(self.spent_label)
        collection_layout.addLayout(collection_header)
        self.badge_collection = BadgeCollection()
        collection_layout.addWidget(self.badge_collection)
        content.addWidget(collection_panel)
        hint = _label("Zapisane saldo uwzględnia rozliczone rundy i zakupy w sklepie. Aktywne zakłady nie zmieniają zapisanej historii.", "hint")
        hint.setWordWrap(True)
        content.addWidget(hint)
        content.addStretch()
        self.message = _label("", "error")
        self.message.setWordWrap(True)
        outer.addWidget(self.message)

        self.refresh_button.clicked.connect(self.refresh_requested)
        self.back_button.clicked.connect(self.back_requested)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.back_requested)
        self.reset()

    def _section(self, layout, title, metrics):
        layout.addWidget(_label(title, "section"))
        row = QHBoxLayout()
        row.setSpacing(7)
        for key, caption in metrics:
            card = QFrame()
            card.setProperty("metric", True)
            column = QVBoxLayout(card)
            column.setContentsMargins(10, 7, 10, 7)
            column.setSpacing(3)
            label = _label(caption)
            label.setProperty("metricTitle", True)
            label.setWordWrap(True)
            value = _label("—")
            value.setProperty("metricValue", True)
            value.setAccessibleName(caption)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            column.addWidget(label)
            column.addWidget(value)
            self.values[key] = value
            row.addWidget(card, 1)
        layout.addLayout(row)

    def set_data(self, profile, stats, badges, spent):
        self.player_label.setText(profile.name)
        self.balance_label.setText(f"{profile.balance}$")
        for key in ("total_rounds", "profitable_rounds", "total_bets", "winning_bets"):
            self.values[key].setText(str(getattr(stats, key)))
        for key in ("total_stake", "total_payout", "biggest_payout"):
            self.values[key].setText(f"{getattr(stats, key)}$")
        self.values["net_profit"].setText(f"{stats.net_profit:+}$")
        color = "#72F5BA" if stats.net_profit > 0 else "#FF8E9B" if stats.net_profit < 0 else "#F0EDE5"
        self.values["net_profit"].setStyleSheet(f"color: {color};")
        self.values["win_rate"].setText(f"{stats.win_rate:.2f}%")
        self.values["bet_win_rate"].setText(f"{stats.bet_win_rate:.2f}%")
        self.badge_count_label.setText(f"Posiadane: {len(badges)}")
        self.spent_label.setText(f"Wydano w sklepie: {spent}$")
        self.badge_collection.set_badges(badges)
        self.no_rounds_label.setVisible(stats.total_rounds == 0)
        self.message.clear()

    def set_busy(self, busy):
        self.refresh_button.setEnabled(not busy)
        self.back_button.setEnabled(not busy)

    def show_error(self, message):
        self.message.setText(message)

    def reset(self):
        self.player_label.setText("—")
        self.balance_label.setText("—")
        for value in self.values.values():
            value.setText("—")
        self.values["net_profit"].setStyleSheet("")
        self.badge_count_label.setText("Posiadane: —")
        self.spent_label.setText("Wydano w sklepie: —")
        self.badge_collection.set_badges(())
        self.no_rounds_label.hide()
        self.message.clear()
