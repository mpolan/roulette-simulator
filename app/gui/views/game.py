"""Trwały widok stołu, selektora i koszyka Etapu 3."""

from PySide6.QtCore import QEvent, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from domain.bet import BetType
from gui.widgets.bet_cart import BetCart
from gui.widgets.betting_table import BettingTable
from gui.widgets.chip_picker import ChipPicker


class GameView(QWidget):
    back_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("gameView")
        self.setStyleSheet("QWidget#gameView { background: #080D14; } "
                           "QComboBox { background: #17232D; border: 1px solid #A58B58; "
                           "border-radius: 4px; padding: 4px 8px; min-height: 22px; } "
                           "QComboBox:focus { border: 2px solid #F5D58C; } "
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
        header.addWidget(self.balance_label)
        layout.addLayout(header)
        self.table = BettingTable()
        self.table.field_activated.connect(controller.activate_field)
        layout.addWidget(self.table, 3)

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
        self.remove_button.setToolTip("Usuń zaznaczoną pozycję. W koszyku: Delete lub dwuklik.")
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
        self.spin_button.setToolTip("Rozliczanie rundy i animowane koło będą dostępne w Etapie 4.")
        footer.addWidget(self.stake_label, 1)
        footer.addWidget(self.spin_button)
        right.addLayout(footer)
        dashboard.addWidget(cart_panel, 1)
        layout.addLayout(dashboard, 2)
        self.message = QLabel("SPIN: dostępny od Etapu 4. Możesz obstawiać i usuwać zakłady.")
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setProperty("role", "hint")
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(20)
        layout.addWidget(self.message)

        self.shortcuts = []
        for sequence, callback in (("Escape", self.back_requested.emit),
                                   ("Alt+C", self._toggle_mode),
                                   ("Ctrl+Return", controller.confirm_classic)):
            self._shortcut(sequence, callback)
        for index in range(5):
            self._shortcut(f"Alt+{index + 1}", lambda i=index: self._choose_chip_index(i))
        for button in self.findChildren(QPushButton):
            button.installEventFilter(self)
        controller.state_changed.connect(self.refresh)
        controller.error.connect(self.show_error)
        self.refresh()

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
        for widget in (self.mode_combo, self.betting_controls, self.table, self.cart):
            widget.setEnabled(not locked)
        self.back_button.setEnabled(not locked)
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
        self._text(self.message, "Obstawianie zablokowane. Dokończ bieżącą operację." if locked else
                   "SPIN: dostępny od Etapu 4. Możesz obstawiać i usuwać zakłady.")
