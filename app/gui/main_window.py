from PySide6.QtCore import QEvent, Qt, Slot
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget

from gui.controllers.application_controller import ApplicationController
from gui.controllers.game_controller import GameController
from gui.views.game import GameView
from gui.views.profiles import ProfilesView
from gui.views.menu import MenuView


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
        self.game_controller = GameController(self.controller, self)
        self.game_view = GameView(self.game_controller)
        self.stack.addWidget(self.profiles_view)
        self.stack.addWidget(self.menu_view)
        self.stack.addWidget(self.game_view)
        self._started = False
        self._shutdown_complete = False
        self.profiles_view.create_requested.connect(self.controller.create_profile)
        self.profiles_view.select_requested.connect(self.controller.select_profile)
        self.profiles_view.refresh_requested.connect(self.refresh_profiles)
        self.profiles_view.back_requested.connect(self.show_menu)
        self.profiles_view.exit_requested.connect(self.close)
        self.menu_view.change_profile_requested.connect(self.show_profiles)
        self.menu_view.game_requested.connect(self.show_game)
        self.game_view.back_requested.connect(self.show_menu)
        self.menu_view.exit_requested.connect(self.close)
        self.controller.profiles_changed.connect(self.profiles_view.set_profiles)
        self.controller.session_changed.connect(self._session_changed)
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
        self.show_menu()
        self._update_state()

    def _show_error(self, message):
        self.profiles_view.message.setText(message)
        self.statusBar().showMessage(message)

    def _game_changed(self):
        if self.controller.session is not None:
            self.menu_view.set_session(self.controller.session)
        self._update_state()

    def _update_state(self, *_):
        busy = self.controller.busy
        blocked = self.controller.blocked()
        self.profiles_view.set_state(
            busy, self.controller.session is not None, blocked,
            self.controller.blocked_reason(), back_blocked=self.controller.navigation_blocked(),
        )
        self.menu_view.set_blocked(blocked, self.controller.blocked_reason())
        self.menu_view.game_button.setEnabled(
            self.controller.session is not None and not self.controller.navigation_blocked()
        )

    def show_game(self):
        if self.controller.session is None or self.controller.navigation_blocked():
            self.statusBar().showMessage(self.controller.blocked_reason())
            return
        self.game_controller.refresh()
        self.stack.setCurrentWidget(self.game_view)
        self.game_view.table.setFocus()

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
        else:
            event.ignore()
            if not self.controller.shutdown():
                self.statusBar().showMessage(self.controller.blocked_reason())

    def _finish_close(self):
        self._shutdown_complete = True
        self.close()
