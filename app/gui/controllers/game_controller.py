"""Intencje obstawiania; stan gry i walidacja pozostają w Game."""

from PySide6.QtCore import QObject, Signal

from domain.bet import Bet, BetType


class GameController(QObject):
    state_changed = Signal()
    error = Signal(str)

    def __init__(self, application_controller=None, parent=None):
        super().__init__(parent)
        self.application_controller = application_controller
        self.session = None
        self.mode = "CHIPS"
        self.chip_value = 25
        self.kind = BetType.RED
        self.group = 1
        self.amount_text = ""
        self.selected_numbers = set()
        if application_controller is not None:
            application_controller.busy_changed.connect(self.refresh)

    @property
    def betting_locked(self):
        return (self.session is None or self.session.has_pending_round or
                (self.application_controller is not None and
                 self.application_controller.navigation_blocked()))

    def set_session(self, session):
        if session is not self.session:
            self.session = session
            self.mode = "CHIPS"
            self.kind = BetType.RED
            self.group = 1
            self.amount_text = ""
            self.selected_numbers.clear()
            values = session.game.CHIP_VALUES if session is not None else ()
            if values and self.chip_value not in values:
                self.chip_value = values[0]
        self.refresh()

    def refresh(self, *_):
        self.state_changed.emit()

    def set_mode(self, mode):
        if self.betting_locked or mode not in ("CHIPS", "CLASSIC"):
            return False
        if mode != self.mode:
            self.mode = mode
            self.selected_numbers.clear()
            self.refresh()
        return True

    def select_chip(self, value):
        if self.betting_locked or value not in self.session.game.CHIP_VALUES:
            return False
        if value != self.chip_value:
            self.chip_value = value
            self.refresh()
        return True

    def set_kind(self, kind):
        if self.betting_locked:
            return False
        self.kind = kind
        if kind != BetType.STRAIGHT:
            self.selected_numbers.clear()
        self.refresh()
        return True

    def set_group(self, group):
        if self.betting_locked:
            return False
        self.group = group
        self.refresh()
        return True

    def set_amount(self, text):
        if self.betting_locked:
            return False
        self.amount_text = text
        self.refresh()
        return True

    def _apply(self, operation, after_success=None):
        if self.betting_locked:
            return False
        try:
            operation()
        except ValueError as exc:
            messages = {
                "Maximum 5 chips per field": "Osiągnięto limit żetonów na tym polu.",
                "No chips on this field": "Na tym polu nie ma żetonów do usunięcia.",
                "Insufficient balance": "Niewystarczające saldo.",
                "Amount must be greater than zero": "Stawka musi być większa od zera.",
            }
            self.error.emit(messages.get(str(exc), f"Nie można zmienić zakładu: {exc}"))
            return False
        if after_success is not None:
            after_success()
        self.refresh()
        return True

    def activate_field(self, kind, selection=None, remove=False):
        if self.betting_locked:
            return False
        if self.mode == "CHIPS":
            game = self.session.game
            return self._apply(lambda: game.remove_chip(kind, selection) if remove else
                               game.place_chip(kind, self.chip_value, selection))
        if remove:
            return False
        self.kind = kind
        if kind == BetType.STRAIGHT:
            self.selected_numbers.symmetric_difference_update({selection})
        else:
            self.selected_numbers.clear()
            if selection is not None:
                self.group = selection
        self.refresh()
        return True

    def confirm_classic(self):
        if self.betting_locked or self.mode != "CLASSIC":
            return False
        try:
            amount = int(self.amount_text)
        except ValueError:
            self.error.emit("Podaj całkowitą stawkę na każde wybrane pole.")
            return False
        if self.kind == BetType.STRAIGHT:
            if not self.selected_numbers:
                self.error.emit("Zaznacz co najmniej jedną liczbę na stole.")
                return False
            bets = [Bet(amount, self.kind, number) for number in sorted(self.selected_numbers)]
        else:
            selection = self.group if self.kind in (BetType.DOZEN, BetType.COLUMN) else None
            bets = [Bet(amount, self.kind, selection)]
        return self._apply(lambda: self.session.game.place_bets(bets), self.selected_numbers.clear)

    def remove_bet(self, bet):
        if self.betting_locked:
            return False
        # Spóźnione kliknięcie nie może usunąć równej, ale innej pozycji.
        if not any(active is bet for active in self.session.game.current_bets):
            return False
        return self._apply(lambda: self.session.game.remove_bet(bet))
