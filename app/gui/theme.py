"""Wspólny motyw Qt oparty na palecie dotychczasowego Obsidian Royale."""

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication


STYLESHEET = """
QWidget { color: #F0EDE5; font-family: "Segoe UI"; font-size: 14px; }
QMainWindow, QWidget#profilesView, QWidget#menuView, QWidget#menuBody { background: #080D14; }
QFrame[panel="true"] {
    background: #121D27; border: 1px solid #34424E; border-radius: 10px;
}
QLabel { background: transparent; border: none; }
QLabel#titleLabel { color: #F5D58C; font-size: 32px; font-weight: 700; }
QLabel#subtitleLabel { color: #AEBBBE; font-size: 15px; }
QLabel#balanceLabel { color: #F5D58C; font-size: 26px; font-weight: 600; }
QLabel#playerLabel { font-size: 20px; font-weight: 600; }
QLabel[role="section"] { color: #F5D58C; font-size: 16px; font-weight: 600; }
QLabel[role="hint"] { color: #AEBBBE; }
QLabel[role="error"] { color: #FF8E9B; }
QPushButton {
    background: #17232D; border: 2px solid #34424E; border-radius: 6px;
    padding: 10px 16px; min-height: 22px; text-align: left;
}
QPushButton:hover { background: #243442; border-color: #A58B58; }
QPushButton:focus { border-color: #F5D58C; }
QPushButton:pressed { background: #30463F; }
QPushButton[variant="primary"] { background: #E8C477; color: #080D14; font-weight: 600; }
QPushButton[variant="primary"]:hover { background: #F5D58C; }
QPushButton[variant="primary"]:focus { border-color: #F0EDE5; }
QPushButton[variant="primary"]:pressed { background: #B99755; }
QPushButton[variant="danger"] { background: #391822; border-color: #6A3442; }
QPushButton[variant="danger"]:hover { background: #641E2B; border-color: #FF8E9B; }
QPushButton[variant="danger"]:focus { border-color: #F5D58C; }
QPushButton:disabled {
    background: #101923; color: #78838B; border-color: #26333E;
}
QLineEdit, QListWidget {
    background: #0C141D; border: 2px solid #34424E; border-radius: 6px;
    selection-background-color: #30463F; selection-color: #F5D58C;
}
QLineEdit { padding: 9px 12px; min-height: 24px; }
QLineEdit:focus, QListWidget:focus { border-color: #F5D58C; }
QLineEdit:disabled, QListWidget:disabled { color: #78838B; border-color: #26333E; }
QListWidget { padding: 6px; outline: none; }
QListWidget::item { padding: 12px; border: 1px solid transparent; border-radius: 4px; }
QListWidget::item:hover { background: #17232D; }
QListWidget::item:selected { background: #243442; color: #F5D58C; border-color: #A58B58; }
QStatusBar { background: #101923; color: #AEBBBE; border-top: 1px solid #26333E; }
QStatusBar::item { border: none; }
QToolTip { background: #243442; color: #F0EDE5; border: 1px solid #A58B58; padding: 6px; }
QScrollBar:vertical { background: #101923; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #6D5938; min-height: 24px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #A58B58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 11))
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, "#080D14"),
        (QPalette.ColorRole.WindowText, "#F0EDE5"),
        (QPalette.ColorRole.Base, "#0C141D"),
        (QPalette.ColorRole.AlternateBase, "#121D27"),
        (QPalette.ColorRole.Text, "#F0EDE5"),
        (QPalette.ColorRole.Button, "#17232D"),
        (QPalette.ColorRole.ButtonText, "#F0EDE5"),
        (QPalette.ColorRole.Highlight, "#30463F"),
        (QPalette.ColorRole.HighlightedText, "#F5D58C"),
        (QPalette.ColorRole.PlaceholderText, "#AEBBBE"),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
