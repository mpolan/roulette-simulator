"""Prezentacja kolejności i gotowych wartości z LeaderboardService."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from services.leaderboard_service import LeaderboardService


def _label(text="", role=None):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        label.setProperty("role", role)
    return label


class LeaderboardView(QWidget):
    refresh_requested = Signal(str)
    back_requested = Signal()

    SORT_LABELS = (
        "Zysk netto", "Najaktywniejsi — liczba rund",
        "Skuteczność — rundy z zyskiem", "Kolekcjonerzy — kupione odznaki",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leaderboardView")
        self.setStyleSheet("""
            QWidget#leaderboardView { background: #080D14; }
            QPushButton { padding: 6px 12px; min-height: 22px; }
            QComboBox { background: #17232D; border: 2px solid #34424E; border-radius: 6px;
                        padding: 6px 10px; min-height: 22px; }
            QComboBox:focus { border-color: #F5D58C; }
            QComboBox QAbstractItemView { background: #121D27; selection-background-color: #30463F; }
            QTableWidget { background: #0C141D; alternate-background-color: #121D27;
                           border: 1px solid #34424E; border-radius: 6px; gridline-color: #26333E;
                           selection-background-color: #30463F; selection-color: #F0EDE5; }
            QTableWidget:focus { border-color: #F5D58C; }
            QHeaderView::section { background: #17232D; color: #F5D58C; padding: 8px 5px;
                                   border: none; border-bottom: 1px solid #A58B58; font-weight: 600; }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 8)
        outer.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(_label("LEADERBOARD", "section"), 1)
        self.refresh_button = QPushButton("Odśwież")
        self.refresh_button.setAccessibleName("Odśwież ranking")
        self.back_button = QPushButton("Powrót do menu")
        header.addWidget(self.refresh_button)
        header.addWidget(self.back_button)
        outer.addLayout(header)

        controls = QFrame()
        controls.setProperty("panel", True)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 9, 12, 9)
        controls_layout.addWidget(_label("KRYTERIUM", "hint"))
        self.sort_combo = QComboBox()
        self.sort_combo.setAccessibleName("Kryterium rankingu")
        for caption, field in zip(self.SORT_LABELS, LeaderboardService.SORT_FIELDS):
            self.sort_combo.addItem(caption, field)
        controls_layout.addWidget(self.sort_combo, 1)
        outer.addWidget(controls)
        self.rules_label = _label("", "hint")
        self.rules_label.setWordWrap(True)
        outer.addWidget(self.rules_label)
        self.position_label = _label("", "section")
        self.position_label.setWordWrap(True)
        outer.addWidget(self.position_label)

        self.table = QTableWidget(0, 7)
        self.table.setAccessibleName("Ranking graczy")
        self.table.setHorizontalHeaderLabels(("#", "Gracz", "Zysk netto", "Rundy", "Skuteczność", "Odznaki", "Saldo"))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setSortingEnabled(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(40)
        outer.addWidget(self.table, 1)
        self.message = _label("", "hint")
        self.message.setWordWrap(True)
        outer.addWidget(self.message)
        self.refresh_button.clicked.connect(lambda: self.refresh_requested.emit(self.sort_by))
        self.back_button.clicked.connect(self.back_requested)
        self.sort_combo.currentIndexChanged.connect(self._sort_changed)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.back_requested)
        self.reset()

    @property
    def sort_by(self):
        return self.sort_combo.currentData()

    def _update_rules(self):
        if self.sort_by == "badge_count":
            rules = "Minimum 1 kupiona odznaka. Największe kolekcje na górze."
        elif self.sort_by == "win_rate":
            rules = f"Minimum {LeaderboardService.MIN_ROUNDS_FOR_WIN_RATE} rozegranych rund."
        else:
            rules = "Minimum 1 rozegrana runda."
        self.rules_label.setText(rules + " Ranking lokalny. Saldo nie wpływa na pozycję.")

    def _sort_changed(self):
        self.table.setRowCount(0)
        self.position_label.clear()
        self.message.clear()
        self._update_rules()
        self.refresh_requested.emit(self.sort_by)

    def set_data(self, entries, active_player_id):
        self.table.setRowCount(len(entries))
        active_position = None
        for row, entry in enumerate(entries):
            position = row + 1
            active = entry.player_id == active_player_id
            if active:
                active_position = position
            badges = " ".join(badge.symbol for badge in entry.badges)
            badge_names = ", ".join(f"{badge.symbol} {badge.name}" for badge in entry.badges)
            name = f"{badges} {entry.player_name}" if badges else entry.player_name
            if active:
                name += " (Ty)"
            cells = (str(position), name, f"{entry.net_profit:+}$", str(entry.total_rounds),
                     f"{entry.win_rate:.2f}%", str(entry.badge_count), f"{entry.balance}$")
            for column, value in enumerate(cells):
                item = self.table.item(row, column)
                if item is None:
                    item = QTableWidgetItem()
                    self.table.setItem(row, column, item)
                item.setText(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |
                                      (Qt.AlignmentFlag.AlignLeft if column == 1 else Qt.AlignmentFlag.AlignCenter))
                color = "#F0EDE5"
                if column == 0:
                    color = {1: "#F5D58C", 2: "#C5CFDA", 3: "#D39A71"}.get(position, "#AEBBBE")
                elif column == 2:
                    color = "#72F5BA" if entry.net_profit > 0 else "#FF8E9B" if entry.net_profit < 0 else "#F0EDE5"
                item.setForeground(QBrush(QColor(color)))
                item.setBackground(QBrush(QColor("#194B40")) if active else QBrush())
                font = item.font()
                font.setBold(active or (column == 0 and position <= 3))
                item.setFont(font)
                item.setToolTip(entry.player_name + (f"\n{badge_names}" if badge_names else "") if column == 1 else "")
                item.setData(Qt.ItemDataRole.UserRole, entry.player_id)

        threshold = LeaderboardService.MIN_ROUNDS_FOR_WIN_RATE
        if active_position is not None:
            position_text = f"Twoja pozycja: #{active_position} / {len(entries)}"
        elif self.sort_by == "badge_count":
            position_text = "Kup odznakę w Prestige Shop, aby dołączyć do rankingu kolekcjonerów."
        elif self.sort_by == "win_rate":
            position_text = f"Twój profil potrzebuje co najmniej {threshold} rund, aby wejść do tego rankingu."
        else:
            position_text = "Rozegraj pierwszą rundę, aby dołączyć do rankingu."
        self.position_label.setText(position_text)
        if entries:
            self.message.setText(f"Graczy w rankingu: {len(entries)}. Twój profil jest oznaczony jako (Ty).")
        elif self.sort_by == "badge_count":
            self.message.setText("Brak zakupionych odznak. Pierwszą znajdziesz w Prestige Shop.")
        elif self.sort_by == "win_rate":
            self.message.setText(f"Brak graczy z co najmniej {threshold} rundami. Zmień kryterium lub rozegraj więcej rund.")
        else:
            self.message.setText("Brak wyników. Rozegraj i zapisz pierwszą rundę, aby pojawić się w rankingu.")
        self.message.setStyleSheet("")

    def set_busy(self, busy):
        self.sort_combo.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy)
        self.back_button.setEnabled(not busy)

    def show_error(self, message):
        self.message.setStyleSheet("color: #FF8E9B;")
        self.message.setText(message)

    def reset(self):
        self.sort_combo.blockSignals(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.blockSignals(False)
        self.table.setRowCount(0)
        self.position_label.clear()
        self.message.clear()
        self.message.setStyleSheet("")
        self._update_rules()
