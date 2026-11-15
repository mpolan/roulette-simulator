from PySide6.QtCore import QCoreApplication, QEvent

from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository


def test_initial_size_and_single_game_status(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Komunikat")
    window = MainWindow()
    available = window.screen().availableGeometry()
    assert window.width() == max(740, min(1360, available.width()))
    assert window.height() == max(560, min(900, available.height() - 40))
    window.show()
    try:
        window.controller.select_profile(player.id)
        wait_until(lambda: not window.controller.busy)
        window.show_game()
        assert not window.game_view.message.isVisible()
        assert window.statusBar().currentMessage() == window.game_view.message.text()
        window.game_controller.status_message = "Koło w ruchu…"
        window.game_controller.refresh()
        assert window.statusBar().currentMessage() == "Koło w ruchu…"
        assert not window.game_view.message.isVisible()
    finally:
        window.close()
        wait_until(lambda: not window.isVisible())
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
