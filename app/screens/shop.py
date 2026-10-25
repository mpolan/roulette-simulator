import sqlite3

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from domain.badge import Badge
from services.game_session import GameSession
from widgets.badge_label import badge_label


class BadgeCard(Vertical):
    def __init__(self, badge: Badge) -> None:
        super().__init__(classes="badge-card")
        self.badge = badge

    def compose(self) -> ComposeResult:
        badge = self.badge
        yield Static(badge_label(badge), classes="badge-title", markup=False)
        yield Static(badge.description, classes="badge-description", markup=False)
        yield Static(f"Cena: {badge.price}$", classes="badge-price")
        yield Static("", classes="badge-state")
        yield Button("Kup", id=f"buy-{badge.id}", classes="buy-badge", disabled=True)

    def update_state(self, owned: bool, balance: int, blocked: bool) -> None:
        self.set_class(owned, "owned")
        state = self.query_one(".badge-state", Static)
        button = self.query_one(Button)
        button.disabled = owned or blocked or balance < self.badge.price
        if owned:
            state.update("POSIADANA")
            button.label = "POSIADANA"
        elif blocked:
            state.update("Zakup chwilowo niedostępny")
            button.label = "Kup"
        elif balance < self.badge.price:
            state.update(f"Brakuje {self.badge.price - balance}$")
            button.label = "Brak środków"
        else:
            state.update("Dostępna do zakupu")
            button.label = "Kup"


class ShopScreen(Screen):
    BINDINGS = [("escape", "back", "Menu główne")]

    def __init__(self, session: GameSession) -> None:
        super().__init__()
        self.session = session
        self._owned_ids: set[str] = set()
        self._collection_loaded = False
        self._buying = False

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="shop-panel"):
            yield Static("PRESTIGE SHOP", classes="panel-title")
            yield Static(self.session.game.player.name, id="shop-player", markup=False)
            yield Static("", id="shop-balance")
            yield Static("Odznaki są kosmetyczne. Nie zmieniają szans wygranej ani zasad ruletki.", classes="panel-hint")
            with Horizontal(classes="shop-actions"):
                yield Button("Odśwież", id="shop-refresh")
                yield Button("Do menu", id="shop-back", tooltip="Powrót do menu głównego")
            yield Static("", id="shop-message", markup=False)
            for badge in self.app.shop.get_catalog():
                yield BadgeCard(badge)

    def on_mount(self) -> None:
        self.refresh_shop()
        self.query_one("#shop-back", Button).focus()

    def blocked_reason(self) -> str:
        if self.session.has_pending_round:
            return "Najpierw ponów zapis rundy w widoku gry. Do tego czasu zakupy są zablokowane."
        if self.session.game.current_bets:
            return "Masz aktywne zakłady. Rozlicz lub usuń je w grze przed zakupem odznaki."
        return ""

    def show_message(self, text: str, error: bool = False) -> None:
        message = self.query_one("#shop-message", Static)
        message.display = bool(text)
        message.update(text)
        message.set_class(error, "error-message")
        message.set_class(bool(text) and not error, "shop-success")

    def update_controls(self) -> None:
        balance = self.session.game.player.balance
        self.query_one("#shop-balance", Static).update(f"Dostępne saldo: {balance}$")
        blocked = bool(self.blocked_reason()) or not self._collection_loaded or self._buying
        for card in self.query(BadgeCard):
            card.update_state(card.badge.id in self._owned_ids, balance, blocked)

    @on(Button.Pressed, "#shop-refresh")
    def refresh_shop(self) -> None:
        try:
            owned = self.app.shop.get_owned_badges(self.session.player_id)
        except (sqlite3.Error, OSError, LookupError, ValueError) as error:
            self._collection_loaded = False
            self.show_message(f"Nie można odczytać kolekcji: {error}. Spróbuj odświeżyć.", error=True)
        else:
            self._owned_ids = {badge.id for badge in owned}
            self._collection_loaded = True
            reason = self.blocked_reason()
            self.show_message(reason, error=bool(reason))
        self.update_controls()

    @on(Button.Pressed, ".buy-badge")
    def buy_badge(self, event: Button.Pressed) -> None:
        event.stop()
        card = event.button.parent
        if not isinstance(card, BadgeCard) or self._buying or not self._collection_loaded:
            return
        reason = self.blocked_reason()
        if reason:
            self.show_message(reason, error=True)
            self.update_controls()
            return
        if card.badge.id in self._owned_ids:
            self.show_message("Ta odznaka jest już w Twojej kolekcji.", error=True)
            return

        self._buying = True
        self.update_controls()
        try:
            purchase = self.app.shop.buy_badge(self.session, card.badge.id)
        except (sqlite3.Error, OSError, LookupError, ValueError, RuntimeError) as error:
            messages = {
                "You cannot buy this badge": "Nie masz wystarczających środków.",
                "Player already owns this badge": "Ta odznaka jest już w Twojej kolekcji.",
                "Badge does not exist": "Wybrana odznaka nie jest dostępna.",
            }
            detail = messages.get(str(error), str(error))
            self.refresh_shop()
            self.show_message(f"Nie udało się kupić odznaki: {detail}", error=True)
            self.notify("Zakup nie został zrealizowany.", severity="error")
        else:
            self._owned_ids.add(purchase.badge_id)
            self.show_message(f"Kupiono {card.badge.name}.")
            self.notify(f"Kupiono {card.badge.name}.")
        finally:
            self._buying = False
            self.update_controls()
            target = event.button if not event.button.disabled else self.query_one("#shop-back", Button)
            self.call_after_refresh(target.focus)

    @on(Button.Pressed, "#shop-back")
    def action_back(self) -> None:
        self.app.pop_screen()
