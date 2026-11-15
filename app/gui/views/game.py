"""Trwały widok stołu, koła i wyniku rundy."""

from PySide6.QtCore import QEvent, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from domain.bet import BetType
from gui.widgets.bet_cart import BetCart
from gui.widgets.betting_table import BettingTable
from gui.widgets.chip_picker import ChipPicker
from gui.widgets.roulette_wheel import RouletteWheel


class GameView(QWidget):
    back_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._session = None
        self.setObjectName("gameView")
        self.setStyleSheet("QWidget#gameView { background: #080D14; } "
                           "QComboBox { background: #17232D; border: 2px solid #A58B58; "
                           "border-radius: 4px; padding: 4px 8px; min-height: 22px; } "
                           "QComboBox:focus { border: 2px solid #F5D58C; } "
                           "QComboBox:disabled { color: #78838B; background: #101923; border-color: #26333E; } "
                           "QComboBox QAbstractItemView { background: #17232D; color: #F0EDE5; } "
                           "QPushButton { padding: 5px 10px; min-height: 20px; } "
                           "QLineEdit { padding: 4px 8px; min-height: 22px; } "
                           "QListWidget::item { padding: 5px 8px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(7)
        header = QHBoxLayout()
        self.back_button = QPushButton("Menu · Esc")
        self.back_button.clicked.connect(self.back_requested)
        self.player_label = QLabel()
        self.player_label.setTextFormat(Qt.TextFormat.PlainText)
        self.player_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.balance_label = QLabel("Saldo: —")
        self.balance_label.setProperty("role", "section")
        header.addWidget(self.back_button)
        header.addWidget(self.player_label, 1)
        self.result_button = QPushButton("Ostatni wynik")
        self.result_button.clicked.connect(self.show_result)
        header.addWidget(self.result_button)
        header.addWidget(self.balance_label)
        layout.addLayout(header)
        self.body = QStackedWidget()
        self.betting_page = QWidget()
        betting_layout = QVBoxLayout(self.betting_page)
        betting_layout.setContentsMargins(0, 0, 0, 0)
        betting_layout.setSpacing(7)
        self.body.addWidget(self.betting_page)
        layout.addWidget(self.body, 1)
        self.table = BettingTable()
        self.table.field_activated.connect(controller.activate_field)
        betting_layout.addWidget(self.table, 3)

        dashboard = QHBoxLayout()
        dashboard.setSpacing(12)
        controls = QFrame()
        controls.setProperty("panel", True)
        left = QVBoxLayout(controls)
        left.setContentsMargins(10, 8, 10, 8)
        left.setSpacing(5)
        mode_row = QHBoxLayout()
        mode_label = QLabel("TRYB")
        mode_label.setProperty("role", "section")
        self.mode_combo = QComboBox()
        self.mode_combo.setAccessibleName("Tryb obstawiania")
        for mode in ("CHIPS", "CLASSIC"):
            self.mode_combo.addItem(mode, mode)
        self.mode_combo.currentIndexChanged.connect(lambda index: controller.set_mode(self.mode_combo.itemData(index)))
        self.mode_combo.setToolTip("Alt+C przełącza CHIPS / CLASSIC. Zmiana trybu zachowuje przyjęte zakłady.")
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_combo, 1)
        left.addLayout(mode_row)
        self.betting_controls = QStackedWidget()
        chips_page = QWidget()
        chips_layout = QVBoxLayout(chips_page)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chip_picker = ChipPicker()
        self.chip_picker.chip_selected.connect(controller.select_chip)
        chips_layout.addWidget(self.chip_picker)
        self.chip_hint = QLabel()
        self.chip_hint.setWordWrap(True)
        self.chip_hint.setProperty("role", "hint")
        chips_layout.addWidget(self.chip_hint)
        chips_layout.addStretch()
        self.betting_controls.addWidget(chips_page)

        classic_page = QWidget()
        classic_layout = QVBoxLayout(classic_page)
        classic_layout.setContentsMargins(0, 0, 0, 0)
        classic_layout.setSpacing(4)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(4)
        kind_row = QHBoxLayout()
        self.kind_combo = QComboBox()
        self.kind_combo.setAccessibleName("Typ zakładu CLASSIC")
        for kind in BetType:
            self.kind_combo.addItem(kind.name, kind)
        self.kind_combo.currentIndexChanged.connect(lambda index: controller.set_kind(self.kind_combo.itemData(index)))
        self.group_combo = QComboBox()
        self.group_combo.setAccessibleName("Numer tuzina lub kolumny")
        for group in (1, 2, 3):
            self.group_combo.addItem(str(group), group)
        self.group_combo.currentIndexChanged.connect(lambda index: controller.set_group(self.group_combo.itemData(index)))
        kind_row.addWidget(self.kind_combo, 1)
        kind_row.addWidget(self.group_combo)
        form.addRow("Zakład", kind_row)
        amount_row = QHBoxLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Stawka na pole ($)")
        self.amount_input.setAccessibleName("Stawka na każde zaznaczone pole w dolarach")
        self.amount_input.textChanged.connect(controller.set_amount)
        self.amount_input.returnPressed.connect(controller.confirm_classic)
        self.confirm_button = QPushButton("Postaw")
        self.confirm_button.setProperty("variant", "primary")
        self.confirm_button.setToolTip("Zatwierdź pakiet. Ctrl+Enter lub Enter w polu stawki.")
        self.confirm_button.clicked.connect(controller.confirm_classic)
        amount_row.addWidget(self.amount_input, 1)
        amount_row.addWidget(self.confirm_button)
        form.addRow("Stawka", amount_row)
        classic_layout.addLayout(form)
        self.draft_label = QLabel()
        self.draft_label.setWordWrap(True)
        self.draft_label.setProperty("role", "hint")
        classic_layout.addWidget(self.draft_label)
        classic_layout.addStretch()
        self.betting_controls.addWidget(classic_page)
        left.addWidget(self.betting_controls, 1)
        dashboard.addWidget(controls, 1)

        cart_panel = QFrame()
        cart_panel.setProperty("panel", True)
        right = QVBoxLayout(cart_panel)
        right.setContentsMargins(10, 8, 10, 8)
        right.setSpacing(4)
        cart_header = QHBoxLayout()
        self.cart_title = QLabel("KOSZYK · 0")
        self.cart_title.setProperty("role", "section")
        self.remove_button = QPushButton("Usuń")
        self.remove_button.setToolTip("Usuń jeden ostatni zakład wybranej grupy i zwróć jego stawkę. "
                                     "W koszyku: Delete lub dwuklik.")
        cart_header.addWidget(self.cart_title, 1)
        cart_header.addWidget(self.remove_button)
        right.addLayout(cart_header)
        self.cart = BetCart()
        self.cart.setMinimumHeight(50)
        self.cart.remove_requested.connect(controller.remove_bet)
        self.remove_button.clicked.connect(self.cart.remove_current)
        right.addWidget(self.cart, 1)
        footer = QHBoxLayout()
        self.stake_label = QLabel("Stawka: 0$")
        self.spin_button = QPushButton("SPIN")
        self.spin_button.setEnabled(False)
        self.spin_button.setToolTip("Rozpocznij rundę · Ctrl+Spacja")
        self.spin_button.clicked.connect(controller.spin)
        footer.addWidget(self.stake_label, 1)
        footer.addWidget(self.spin_button)
        right.addLayout(footer)
        dashboard.addWidget(cart_panel, 1)
        betting_layout.addLayout(dashboard, 2)
        self.wheel_page = QWidget()
        wheel_layout = QHBoxLayout(self.wheel_page)
        wheel_layout.setContentsMargins(0, 0, 0, 0)
        self.wheel = RouletteWheel()
        wheel_layout.addWidget(self.wheel, 3)
        result_panel = QFrame()
        result_panel.setProperty("panel", True)
        result_panel.setMinimumWidth(230)
        result_layout = QVBoxLayout(result_panel)
        self.result_title = QLabel("Koło w ruchu…")
        self.result_title.setProperty("role", "section")
        self.result_title.setWordWrap(True)
        self.result_summary = QLabel()
        self.result_summary.setWordWrap(True)
        self.result_bets = QListWidget()
        self.result_bets.setAccessibleName("Rozliczenie poszczególnych zakładów")
        self.next_button = QPushButton("Obstawiaj dalej")
        self.next_button.clicked.connect(self.show_betting)
        for widget in (self.result_title, self.result_summary, self.result_bets, self.next_button):
            result_layout.addWidget(widget, 1 if widget is self.result_bets else 0)
        wheel_layout.addWidget(result_panel, 2)
        self.body.addWidget(self.wheel_page)
        status_row = QHBoxLayout()
        self.message = QLabel()
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setProperty("role", "hint")
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(20)
        self.message.hide()
        status_row.addWidget(self.message, 1)
        self.retry_button = QPushButton("Ponów zapis")
        self.retry_button.clicked.connect(controller.retry_save)
        self.retry_button.setToolTip("Zapisz tę samą rundę ponownie · Ctrl+R")
        status_row.addWidget(self.retry_button)
        layout.addLayout(status_row)

        self.shortcuts = []
        for sequence, callback in (("Escape", self.back_requested.emit),
                                   ("Alt+C", self._toggle_mode),
                                   ("Ctrl+Return", controller.confirm_classic),
                                   ("Ctrl+Space", controller.spin),
                                   ("Ctrl+R", controller.retry_save)):
            self._shortcut(sequence, callback)
        for index in range(5):
            self._shortcut(f"Alt+{index + 1}", lambda i=index: self._choose_chip_index(i))
        for button in self.findChildren(QPushButton):
            button.installEventFilter(self)
        controller.state_changed.connect(self.refresh)
        controller.error.connect(self.show_error)
        controller.animation_requested.connect(self.animate_result)
        controller.round_revealed.connect(self.reveal_result)
        self.wheel.animation_finished.connect(controller.animation_finished)
        self.refresh()

    def show_betting(self):
        if not self.controller.betting_locked:
            self.body.setCurrentWidget(self.betting_page)
            self.table.setFocus()

    def show_result(self):
        if self.controller.result is not None and not self.controller.betting_locked:
            self.body.setCurrentWidget(self.wheel_page)

    def animate_result(self, result):
        self.result_title.setText("Koło w ruchu…")
        self.result_summary.setText("Runda zapisana. Czekamy na zatrzymanie koła.")
        self.result_bets.clear()
        self.body.setCurrentWidget(self.wheel_page)
        self.wheel.start(result)

    def reveal_result(self, result):
        color = {"red": "CZERWONE", "black": "CZARNE", "green": "ZIELONE"}[result.pocket.color.value]
        self.result_title.setText(f"WYNIK · {result.pocket.number} · {color}")
        self.result_summary.setText(f"Stawka: {result.total_stake}$\n"
                                    f"Wypłata: {result.total_payout}$\n"
                                    f"Bilans rundy: {result.net_profit:+d}$")
        self.result_bets.clear()
        groups = {}
        for entry in result.bet_results:
            key = (entry.bet.bet_type, entry.bet.selection, entry.won)
            group = groups.setdefault(key, [0, 0, 0])
            group[0] += 1
            group[1] += entry.bet.amount
            group[2] += entry.payout
        for (kind, selection, won), (count, stake, payout) in groups.items():
            label = kind.name + (f" {selection}" if selection is not None else "")
            outcome = "WYGRANY" if won else "PRZEGRANY"
            text = f"{outcome} · {label} · zakładów: {count}\nStawka {stake}$ · wypłata {payout}$"
            self.result_bets.addItem(text)
            item = self.result_bets.item(self.result_bets.count() - 1)
            item.setToolTip(text)
            item.setForeground(QColor("#72F5BA" if won else "#FF8E9B"))
        self.next_button.setFocus()

    def eventFilter(self, watched, event):
        if (isinstance(watched, QPushButton) and watched.isEnabled() and
                event.type() == QEvent.Type.KeyPress and
                event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            watched.click()
            return True
        return super().eventFilter(watched, event)

    def _shortcut(self, sequence, callback):
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(callback)
        self.shortcuts.append(shortcut)

    def _toggle_mode(self):
        self.controller.set_mode("CLASSIC" if self.controller.mode == "CHIPS" else "CHIPS")

    def _choose_chip_index(self, index):
        if self.controller.session is not None:
            values = self.controller.session.game.CHIP_VALUES
            if index < len(values):
                self.controller.select_chip(values[index])

    def show_error(self, text):
        self.message.setText(text)

    @staticmethod
    def _text(label, text):
        if label.text() != text:
            label.setText(text)

    def refresh(self):
        controller = self.controller
        locked = controller.betting_locked
        app = controller.application_controller
        busy = app is not None and app.busy
        self.spin_button.setEnabled(controller.can_spin)
        self.next_button.setEnabled(not locked)
        self.result_button.setEnabled(controller.result is not None and not locked)
        self.retry_button.setVisible(controller.can_retry or (not busy and controller.session is not None and
                                                             controller.session.has_pending_round))
        self.retry_button.setEnabled(controller.can_retry)
        self._text(self.message, controller.status_message or "Wybierz zakłady i naciśnij SPIN · Ctrl+Spacja.")
        for widget in (self.mode_combo, self.betting_controls, self.table, self.cart):
            widget.setEnabled(not locked)
        self.back_button.setEnabled(not locked)
        if busy:
            self.remove_button.setEnabled(False)
            return
        with QSignalBlocker(self.mode_combo):
            self.mode_combo.setCurrentIndex(self.mode_combo.findData(controller.mode))
        classic = controller.mode == "CLASSIC"
        self.betting_controls.setCurrentIndex(1 if classic else 0)
        with QSignalBlocker(self.kind_combo):
            self.kind_combo.setCurrentIndex(self.kind_combo.findData(controller.kind))
        with QSignalBlocker(self.group_combo):
            self.group_combo.setCurrentIndex(self.group_combo.findData(controller.group))
        self.group_combo.setVisible(controller.kind in (BetType.DOZEN, BetType.COLUMN))
        if self.amount_input.text() != controller.amount_text:
            with QSignalBlocker(self.amount_input):
                self.amount_input.setText(controller.amount_text)
        if controller.session is None:
            self.remove_button.setEnabled(False)
            return
        game = controller.session.game
        if self._session is not controller.session:
            self._session = controller.session
            self.wheel.reset()
            self.result_bets.clear()
            self.result_title.clear()
            self.result_summary.clear()
            self.body.setCurrentWidget(self.betting_page)
        self.wheel.set_pockets(game.wheel.pockets)
        self.chip_picker.set_values(game.CHIP_VALUES)
        self.chip_picker.set_selected(controller.chip_value)
        for button in self.chip_picker.buttons.values():
            button.installEventFilter(self)
        self.table.set_pockets(game.wheel.pockets)
        outside = None
        if classic and controller.kind != BetType.STRAIGHT:
            outside = (controller.kind, controller.group if controller.kind in (BetType.DOZEN, BetType.COLUMN) else None)
        self.table.update_fields(game, controller.selected_numbers if classic else (), outside)
        self.cart.set_bets(game.current_bets)
        self.remove_button.setEnabled(not locked and bool(game.current_bets))
        self._text(self.player_label, game.player.name)
        self.player_label.setToolTip(game.player.name)
        self._text(self.balance_label, f"Saldo: {game.player.balance}$")
        self._text(self.stake_label, f"Stawka: {game.total_stake}$")
        self._text(self.cart_title, f"KOSZYK · {len(game.current_bets)}")
        self._text(self.chip_hint, f"Klik / Enter: +żeton · prawy klik / Delete: −ostatni\n"
                   f"Limit: {game.MAX_CHIPS_PER_FIELD} na pole · Alt+1…5: nominał\n"
                   "Strzałki: wybór pola · Tab: następna kontrolka")
        numbers = sorted(controller.selected_numbers)
        count = len(numbers) if controller.kind == BetType.STRAIGHT else 1
        try:
            amount = int(controller.amount_text)
            cost = f"Koszt: {count} × {amount}$ = {count * amount}$"
        except ValueError:
            cost = "Podaj stawkę na każde zaznaczone pole."
        selection = ", ".join(map(str, numbers[:10]))
        if len(numbers) > 10:
            selection += f"… ({len(numbers)} liczb)"
        draft = f"Liczby: {selection or 'zaznacz na stole'}\n" if controller.kind == BetType.STRAIGHT else ""
        self._text(self.draft_label, draft + cost)
        self.draft_label.setToolTip(", ".join(map(str, numbers)))
