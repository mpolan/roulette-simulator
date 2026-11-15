import sqlite3

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from persistence.player_repository import PlayerRepository
from services.session_factory import create_game_session


class _Worker(QObject):
    finished = Signal(str, object, object, object)

    def __init__(self, players, session_factory):
        super().__init__()
        self.players = players
        self.session_factory = session_factory

    @Slot(str, object)
    def execute(self, action, argument):
        created = None
        try:
            if action == "load":
                result = self.players.get_all_players()
            elif action == "create":
                created = self.players.add_player(argument)
                result = self.session_factory(created.id)
            else:
                result = self.session_factory(argument)
            self.finished.emit(action, result, None, created)
        except Exception as exc:
            self.finished.emit(action, None, exc.with_traceback(None), created)


class ApplicationController(QObject):
    session_changed = Signal(object)
    busy_changed = Signal(bool)
    profiles_changed = Signal(object)
    error = Signal(str)
    shutdown_finished = Signal()
    _request = Signal(str, object)
    _stop = Signal()

    def __init__(self, parent=None, players=None, session_factory=create_game_session):
        super().__init__(parent)
        self.session = None
        self.busy = False
        self.animating = False
        self._closing = False
        self._shutdown_emitted = False
        self._thread = QThread(self)
        self._worker = _Worker(players if players is not None else PlayerRepository(), session_factory)
        self._worker.moveToThread(self._thread)
        self._request.connect(self._worker.execute)
        self._worker.finished.connect(self._finished)
        self._stop.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._confirm_shutdown)
        self._thread.start()

    def blocked(self):
        return (self.busy or self.animating or self._closing or
                (self.session is not None and
                 (bool(self.session.game.current_bets) or self.session.has_pending_round)))

    def navigation_blocked(self):
        return (self.busy or self.animating or self._closing or
                (self.session is not None and self.session.has_pending_round))

    def blocked_reason(self):
        if self.busy:
            return "Trwa operacja. Poczekaj na jej zakończenie."
        if self.animating:
            return "Poczekaj na zakończenie animacji."
        if self._closing:
            return "Trwa zamykanie aplikacji."
        if self.session is not None:
            if self.session.has_pending_round:
                return "Najpierw zapisz oczekującą rundę."
            if self.session.game.current_bets:
                return "Najpierw rozlicz lub usuń aktywne zakłady."
        return ""

    def _submit(self, action, value=None):
        if self._closing or self.busy or (action != "load" and self.blocked()):
            return False
        self.busy = True
        self.busy_changed.emit(True)
        self._request.emit(action, value)
        return True

    def load_profiles(self):
        return self._submit("load")

    def create_profile(self, name):
        if self.blocked():
            return False
        name = name.strip()
        if not name:
            self.error.emit("Podaj nazwę gracza.")
            return False
        if len(name) > 40:
            self.error.emit("Nazwa gracza może mieć najwyżej 40 znaków.")
            return False
        return self._submit("create", name)

    def select_profile(self, player_id):
        return self._submit("select", player_id)

    @Slot(str, object, object, object)
    def _finished(self, action, result, exc, created):
        self.busy = False
        self.busy_changed.emit(False)
        if exc is not None:
            if created is not None:
                self.error.emit(f"Utworzono profil {created.name}, ale nie można go otworzyć: {exc}. Wybierz go z listy.")
                self.load_profiles()
            elif isinstance(exc, sqlite3.IntegrityError) and action == "create":
                self.error.emit("Profil o tej nazwie już istnieje. Wybierz inną nazwę.")
            elif isinstance(exc, LookupError):
                self.error.emit("Nie znaleziono profilu. Odśwież listę i spróbuj ponownie.")
                if action == "select":
                    self.load_profiles()
            else:
                verb = {"load": "odczytać profili", "create": "utworzyć profilu", "select": "otworzyć profilu"}[action]
                self.error.emit(f"Nie można {verb}: {exc}")
            return
        if action == "load":
            self.profiles_changed.emit(result)
        else:
            self.session = result
            self.session_changed.emit(result)

    def shutdown(self):
        if self.blocked():
            return False
        self._closing = True
        self._stop.emit()
        return True

    @Slot()
    def _confirm_shutdown(self):
        # finished może poprzedzać końcowe sprzątanie natywnego wątku.
        # wait(0) jedynie sprawdza stan; nie zatrzymuje pętli GUI.
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._confirm_shutdown)
            return
        if not self._shutdown_emitted:
            self._shutdown_emitted = True
            self.shutdown_finished.emit()
