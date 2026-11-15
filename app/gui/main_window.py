from PySide6.QtCore import QEvent, Qt, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QMessageBox, QPushButton, QStackedWidget

from gui.controllers.application_controller import ApplicationController
from gui.controllers.game_controller import GameController
from gui.views.game import GameView
from gui.views.profiles import ProfilesView
from gui.views.menu import MenuView
from gui.views.statistics import StatisticsView
from gui.views.leaderboard import LeaderboardView


class MainWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.setWindowTitle("Obsidian Royale")
        self.resize(900, 650)
        self.setMinimumSize(740, 560)
        self.controller = controller if controller is not None else ApplicationController(self)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.profiles_view = ProfilesView()
        self.menu_view = MenuView()
        self.statistics_view = StatisticsView()
        self.leaderboard = LeaderboardView()
        self.game_controller = GameController(self.controller, self)
        self.game_view = GameView(self.game_controller)
        self.stack.addWidget(self.profiles_view)
        self.stack.addWidget(self.menu_view)
        self.stack.addWidget(self.game_view)
        self.stack.addWidget(self.statistics_view)
        self.stack.addWidget(self.leaderboard)
        self._started = False
        self._shutdown_complete = False
        self._close_dialog = None
        self._close_shortcuts = []
        for sequence in ("Alt+F4", "Ctrl+Q"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(self.close)
            self._close_shortcuts.append(shortcut)
        self.profiles_view.create_requested.connect(self.controller.create_profile)
        self.profiles_view.select_requested.connect(self.controller.select_profile)
        self.profiles_view.refresh_requested.connect(self.refresh_profiles)
        self.profiles_view.back_requested.connect(self.show_menu)
        self.profiles_view.exit_requested.connect(self.close)
        self.menu_view.change_profile_requested.connect(self.show_profiles)
        self.menu_view.game_requested.connect(self.show_game)
        self.menu_view.statistics_requested.connect(self.show_statistics)
        self.statistics_view.back_requested.connect(self.show_menu)
        self.statistics_view.refresh_requested.connect(self.refresh_statistics)
        self.menu_view.leaderboard_requested.connect(self.show_leaderboard)
        self.leaderboard.back_requested.connect(self.show_menu)
        self.leaderboard.refresh_requested.connect(self._refresh_leaderboard)
        self.game_view.back_requested.connect(self.show_menu)
        self.menu_view.exit_requested.connect(self.close)
        self.controller.profiles_changed.connect(self.profiles_view.set_profiles)
        self.controller.session_changed.connect(self._session_changed)
        self.controller.statistics_changed.connect(self._statistics_changed)
        self.controller.statistics_error.connect(self._statistics_error)
        self.controller.leaderboard_changed.connect(self._leaderboard_changed)
        self.controller.leaderboard_error.connect(self._leaderboard_error)
        self.game_controller.state_changed.connect(self._game_changed)
        self.game_controller.error.connect(self.statusBar().showMessage)
        self.controller.busy_changed.connect(self._update_state)
        self.controller.error.connect(self._show_error)
        self.controller.shutdown_finished.connect(self._finish_close)
        for button in self.findChildren(QPushButton):
            button.installEventFilter(self)
        self._update_state()

    def eventFilter(self, watched, event):
        if (isinstance(watched, QPushButton) and watched.isEnabled()
                and event.type() == QEvent.Type.KeyPress
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            watched.click()
            return True
        return super().eventFilter(watched, event)

    def start(self):
        if not self._started:
            self._started = True
            self.controller.load_profiles()

    @Slot(object)
    def _session_changed(self, session):
        self.profiles_view.message.clear()
        self.statusBar().clearMessage()
        self.profiles_view.name_input.clear()
        self.menu_view.set_session(session)
        self.game_controller.set_session(session)
        self.statistics_view.reset()
        self.leaderboard.reset()
        self.show_menu()
        self._update_state()

    def _show_error(self, message):
        self.profiles_view.message.setText(message)
        self.statusBar().showMessage(message)

    def _game_changed(self):
        if self.controller.session is not None:
            self.menu_view.set_session(self.controller.session)
        message = self.game_controller.status_message
        if not message and self.controller.navigation_blocked():
            message = self.controller.blocked_reason()
        self.statusBar().showMessage(message)
        self._update_state()

    def _update_state(self, *_):
        busy = self.controller.busy
        blocked = self.controller.blocked()
        self.profiles_view.set_state(
            busy, self.controller.session is not None, blocked,
            self.controller.blocked_reason(), back_blocked=self.controller.navigation_blocked(),
        )
        self.menu_view.set_blocked(blocked, self.controller.blocked_reason())
        for button in (self.menu_view.exit_button, self.profiles_view.exit_button):
            button.setEnabled(not self.controller.navigation_blocked())
            button.setToolTip(self.controller.blocked_reason() if not button.isEnabled() else "")
        self.menu_view.game_button.setEnabled(
            self.controller.session is not None and not self.controller.navigation_blocked()
        )
        self.menu_view.statistics_button.setEnabled(
            self.controller.session is not None and not self.controller.navigation_blocked()
        )
        self.statistics_view.set_busy(self.controller.navigation_blocked())
        self.menu_view.leaderboard_button.setEnabled(
            self.controller.session is not None and not self.controller.navigation_blocked()
        )
        self.leaderboard.set_busy(self.controller.navigation_blocked())

    def show_leaderboard(self):
        if self.controller.session is None or self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.stack.setCurrentWidget(self.leaderboard)
        self._refresh_leaderboard(self.leaderboard.sort_by)

    def _refresh_leaderboard(self, sort_by):
        self.controller.load_leaderboard(sort_by)

    def _leaderboard_changed(self, entries):
        self.leaderboard.set_data(entries, self.controller.session.player_id)
        self.leaderboard.sort_combo.setFocus()

    def _leaderboard_error(self, message):
        self.leaderboard.show_error(message)
        self.leaderboard.refresh_button.setFocus()

    def show_statistics(self):
        if self.controller.session is None or self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.stack.setCurrentWidget(self.statistics_view)
        self.refresh_statistics()

    def refresh_statistics(self):
        self.controller.load_statistics()

    def _statistics_changed(self, data):
        self.statistics_view.set_data(*data)
        self.statistics_view.refresh_button.setFocus()

    def _statistics_error(self, message):
        self.statistics_view.show_error(message)
        self.statistics_view.refresh_button.setFocus()

    def show_game(self):
        if self.controller.session is None or self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.game_controller.refresh()
        self.stack.setCurrentWidget(self.game_view)
        if self.game_view.table.isVisible():
            self.game_view.table.setFocus()
        else:
            self.game_view.next_button.setFocus()

    def show_profiles(self):
        if self.controller.blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.stack.setCurrentWidget(self.profiles_view)
        self.refresh_profiles()

    def refresh_profiles(self):
        if self.controller.busy:
            return
        self.profiles_view.message.clear()
        self.statusBar().clearMessage()
        self.controller.load_profiles()

    def show_menu(self):
        self._update_state()
        if self.controller.session is None or self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.menu_view.set_session(self.controller.session)
        self.stack.setCurrentWidget(self.menu_view)
        self.menu_view.game_button.setFocus()

    def closeEvent(self, event):
        if self._shutdown_complete:
            event.accept()
            return
        event.ignore()
        if self._close_dialog is not None:
            self._close_dialog.raise_()
            self._close_dialog.activateWindow()
            return
        if self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        session = self.controller.session
        if session is not None and session.game.current_bets:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Zamknąć Obsidian Royale?")
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText("Masz aktywne zakłady. Anulować je i zamknąć aplikację?")
            dialog.setInformativeText("Stawki zostaną zwrócone. Runda nie zostanie rozegrana.")
            dialog.addButton("Anuluj zakłady i zamknij", QMessageBox.ButtonRole.DestructiveRole)
            back = dialog.addButton("Wróć do gry", QMessageBox.ButtonRole.RejectRole)
            dialog.setDefaultButton(back)
            dialog.setEscapeButton(back)
            dialog.finished.connect(self._close_dialog_finished)
            self._close_dialog = dialog
            dialog.open()
            return
        self.controller.shutdown()

    def _close_dialog_finished(self, _result):
        dialog = self._close_dialog
        self._close_dialog = None
        confirmed = dialog.buttonRole(dialog.clickedButton()) == QMessageBox.ButtonRole.DestructiveRole
        dialog.deleteLater()
        if confirmed:
            # Kontroler ponownie sprawdza pending/busy/animację po decyzji użytkownika.
            if not self.controller.shutdown(cancel_bets=True):
                self.statusBar().showMessage(self.controller.blocked_reason())
            self.game_controller.refresh()
        else:
            self.show_game()

    def _finish_close(self):
        self._shutdown_complete = True
        self.close()
