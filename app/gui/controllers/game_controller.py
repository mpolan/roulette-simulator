"""Intencje obstawiania; stan gry i walidacja pozostają w Game."""

from PySide6.QtCore import QObject, Signal

from domain.bet import Bet, BetType


class GameController(QObject):
    state_changed = Signal()
    error = Signal(str)
    animation_requested = Signal(object)
    round_revealed = Signal(object)

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
        self.animating = False
        self.result = None
        self.status_message = ""
        self._round_requested = False
        if application_controller is not None:
            application_controller.busy_changed.connect(self.refresh)
            if hasattr(application_controller, "round_finished"):
                application_controller.round_finished.connect(self._round_finished)

    @property
    def betting_locked(self):
        return (self.session is None or self._round_requested or self.animating or
                (self.application_controller is not None and
                 self.application_controller.navigation_blocked()) or self.session.has_pending_round)

    @property
    def can_spin(self):
        return (self.application_controller is not None and not self.betting_locked and
                bool(self.session.game.current_bets))

    @property
    def can_retry(self):
        app = self.application_controller
        return (app is not None and self.session is not None and
                not app.busy and not self.animating and not self._round_requested and
                self.session.has_pending_round)

    def set_session(self, session):
        if session is not self.session:
            self.session = session
            self.mode = "CHIPS"
            self.kind = BetType.RED
            self.group = 1
            self.amount_text = ""
            self.selected_numbers.clear()
            self.result = None
            self.status_message = ""
            values = session.game.CHIP_VALUES if session is not None else ()
            if values and self.chip_value not in values:
                self.chip_value = values[0]
        self.refresh()

    def spin(self):
        if not self.can_spin:
            return False
        return self._submit_round(False)

    def retry_save(self):
        if not self.can_retry:
            return False
        return self._submit_round(True)

    def _submit_round(self, retry):
        self._round_requested = True
        self.status_message = "Ponawianie zapisu rundy…" if retry else "Rozliczanie i zapis rundy…"
        if not self.application_controller.submit_round(retry=retry):
            self._round_requested = False
            self.status_message = ""
            self.refresh()
            return False
        return True

    def _round_finished(self, result, exc):
        if not self._round_requested:
            return
        self._round_requested = False
        if exc is not None:
            self.status_message = (f"Nie udało się zapisać rundy: {exc}. Ponów zapis." if self.session.has_pending_round
                                   else f"Nie udało się rozpocząć rundy: {exc}")
            self.refresh()
            self.error.emit(self.status_message)
            return
        self.result = result
        self.selected_numbers.clear()
        self.animating = True
        self.application_controller.animating = True
        self.status_message = "Koło w ruchu…"
        self.refresh()
        self.animation_requested.emit(result)

    def animation_finished(self, result):
        if not self.animating or result is not self.result:
            return
        self.animating = False
        self.application_controller.animating = False
        self.status_message = "Runda zakończona. Możesz obstawiać kolejną rundę."
        self.refresh()
        self.round_revealed.emit(result)

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
