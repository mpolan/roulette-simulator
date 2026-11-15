from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from gui.main_window import MainWindow
from gui.controllers.application_controller import ApplicationController
from persistence.player_repository import PlayerRepository


def close_window(window, wait_until):
    window.close()
    wait_until(lambda: not window.isVisible())


def test_create_profile_keyboard_and_navigation(qapp, initialized_db, wait_until):
    window = MainWindow()
    window.show()
    window.start()
    wait_until(lambda: not window.controller.busy)
    view = window.profiles_view
    view.name_input.setFocus()
    QTest.keyClicks(view.name_input, "  Ala  ")
    QTest.keyClick(view.name_input, Qt.Key.Key_Return)
    wait_until(lambda: window.controller.session is not None)
    session = window.controller.session
    assert session.game.player.name == "Ala"
    assert "Ala" in window.menu_view.player_label.text()
    assert str(session.game.player.balance) in window.menu_view.balance_label.text()
    QTest.mouseClick(window.menu_view.change_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert view.profile_list.count() == 1
    QTest.keyClick(view, Qt.Key.Key_Escape)
    assert window.stack.currentWidget() is window.menu_view
    assert window.controller.session is session
    close_window(window, wait_until)


def test_selection_and_duplicate(qapp, initialized_db, wait_until):
    repository = PlayerRepository()
    repository.add_player("Ala")
    window = MainWindow()
    window.show()
    window.start()
    wait_until(lambda: not window.controller.busy)
    view = window.profiles_view
    view.name_input.setText("Ala")
    QTest.mouseClick(view.create_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert "już istnieje" in view.message.text()
    view.profile_list.setCurrentRow(0)
    view.profile_list.setFocus()
    QTest.keyClick(view.profile_list, Qt.Key.Key_Return)
    wait_until(lambda: window.controller.session is not None)
    close_window(window, wait_until)


def test_blocked_close_and_profile_change(qapp, initialized_db, wait_until):
    profile = PlayerRepository().add_player("Ala")
    window = MainWindow()
    window.show()
    window.start()
    wait_until(lambda: not window.controller.busy)
    window.controller.select_profile(profile.id)
    wait_until(lambda: window.controller.session is not None)
    session = window.controller.session
    window.controller.animating = True
    assert window.controller.blocked()
    assert not window.controller.select_profile(profile.id)
    assert not window.controller.create_profile("Inny")
    window.close()
    qapp.processEvents()
    assert window.isVisible()
    assert window.controller.session is session
    window.controller.animating = False
    close_window(window, wait_until)


def test_created_profile_survives_factory_error(qapp, initialized_db, wait_until):
    def fail(_):
        raise OSError("błąd odczytu")

    controller = ApplicationController(session_factory=fail)
    window = MainWindow(controller)
    window.show()
    window.start()
    wait_until(lambda: not controller.busy)
    window.profiles_view.name_input.setText("Ala")
    window.profiles_view.create_button.click()
    wait_until(lambda: not controller.busy and window.profiles_view.profile_list.count() == 1)
    assert "Utworzono profil Ala" in window.profiles_view.message.text()
    assert len(PlayerRepository().get_all_players()) == 1
    close_window(window, wait_until)



def test_tab_and_active_bet_block(qapp, initialized_db, wait_until):
    from domain.bet import Bet, BetType

    profile = PlayerRepository().add_player("Ala")
    window = MainWindow()
    window.show()
    window.start()
    wait_until(lambda: not window.controller.busy)
    view = window.profiles_view
    view.name_input.setFocus()
    QTest.keyClick(view.name_input, Qt.Key.Key_Tab)
    assert qapp.focusWidget() is view.create_button
    QTest.keyClick(view.create_button, Qt.Key.Key_Backtab, Qt.KeyboardModifier.ShiftModifier)
    assert qapp.focusWidget() is view.name_input
    window.controller.select_profile(profile.id)
    wait_until(lambda: window.controller.session is not None)
    session = window.controller.session
    bet = Bet(5, BetType.RED)
    session.game.place_bet(bet)
    assert window.controller.blocked()
    assert not window.controller.select_profile(profile.id)
    window.close()
    qapp.processEvents()
    assert window.isVisible()
    assert window.controller.session is session
    window._close_dialog.reject()
    session.game.remove_bet(bet)
    close_window(window, wait_until)
