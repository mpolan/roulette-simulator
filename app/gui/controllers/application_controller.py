import sqlite3

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from persistence.shop_repository import ShopRepository
from services.session_factory import create_game_session
from services.stats_service import StatsService
from services.shop_service import ShopService
from services.leaderboard_service import LeaderboardService


class _Worker(QObject):
    finished = Signal(str, object, object, object)

    def __init__(self, players, session_factory):
        super().__init__()
        self.players = players
        self.session_factory = session_factory
        self.stats = StatsService(RoundRepository())
        self.shop = ShopService(ShopRepository())
        self.leaderboard = LeaderboardService(self.players, self.stats, self.shop)

    @Slot(str, object)
    def execute(self, action, argument):
        created = None
        try:
            if action == "load":
                result = self.players.get_all_players()
            elif action == "create":
                created = self.players.add_player(argument)
                result = self.session_factory(created.id)
            elif action == "spin":
                result = argument.spin_and_save()
            elif action == "retry":
                result = argument.save_pending_round()
            elif action == "statistics":
                profile = self.players.get_player(argument)
                if profile is None:
                    raise LookupError("Profil nie istnieje.")
                result = (profile, self.stats.get_player_stats(argument),
                          self.shop.get_owned_badges(argument), self.shop.get_total_spent(argument))
            elif action == "leaderboard":
                result = self.leaderboard.get_leaderboard(argument)
            elif action == "shop":
                result = (self.shop.get_catalog(), self.shop.get_owned_badges(argument))
            elif action == "buy":
                result = self.shop.buy_badge(*argument)
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
    round_finished = Signal(object, object)
    statistics_changed = Signal(object)
    statistics_error = Signal(str)
    leaderboard_changed = Signal(object)
    leaderboard_error = Signal(str)
    shop_changed = Signal(object)
    shop_error = Signal(str)
    purchase_finished = Signal(object, object)
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
                return "Najpierw ponów zapis oczekującej rundy."
            if self.session.game.current_bets:
                return "Najpierw rozlicz lub usuń aktywne zakłady."
        return ""

    def _submit(self, action, value=None):
        if self._closing or self.busy or (action not in ("load", "spin", "retry", "statistics", "leaderboard", "shop") and self.blocked()):
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

    def load_statistics(self):
        if self.session is None or self.navigation_blocked():
            return False
        return self._submit("statistics", self.session.player_id)

    def load_leaderboard(self, sort_by="net_profit"):
        if self.session is None or self.navigation_blocked():
            return False
        return self._submit("leaderboard", sort_by)

    def load_shop(self):
        if self.session is None or self.navigation_blocked():
            return False
        return self._submit("shop", self.session.player_id)

    def buy_badge(self, badge_id):
        if self.session is None or self.blocked():
            return False
        return self._submit("buy", (self.session, badge_id))

    def submit_round(self, retry=False):
        if self._closing or self.busy or self.animating or self.session is None:
            return False
        if retry:
            if not self.session.has_pending_round:
                return False
        elif self.session.has_pending_round or not self.session.game.current_bets:
            return False
        return self._submit("retry" if retry else "spin", self.session)

    @Slot(str, object, object, object)
    def _finished(self, action, result, exc, created):
        self.busy = False
        if action in ("spin", "retry"):
            # Odbiorca ustawia blokadę animacji przed sygnałem końca I/O.
            self.round_finished.emit(result, exc)
            self.busy_changed.emit(False)
            return
        self.busy_changed.emit(False)
        if action == "buy":
            self.purchase_finished.emit(result, exc)
            return
        if action == "shop":
            if exc is not None:
                self.shop_error.emit(f"Nie można odczytać sklepu i kolekcji: {exc}. Spróbuj odświeżyć.")
            else:
                self.shop_changed.emit(result)
            return
        if action == "leaderboard":
            if exc is not None:
                self.leaderboard_error.emit(f"Nie można odczytać rankingu: {exc}. Spróbuj odświeżyć.")
            else:
                self.leaderboard_changed.emit(result)
            return
        if action == "statistics":
            if exc is not None:
                self.statistics_error.emit(f"Nie można odczytać statystyk i kolekcji: {exc}")
            else:
                self.statistics_changed.emit(result)
            return
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

    def shutdown(self, *, cancel_bets=False):
        if self.navigation_blocked():
            return False
        if self.session is not None and self.session.game.current_bets:
            if not cancel_bets:
                return False
            game = self.session.game
            for bet in game.current_bets:
                game.remove_bet(bet)
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
