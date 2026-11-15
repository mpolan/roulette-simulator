from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea


class MenuView(QWidget):
    game_requested = Signal()
    statistics_requested = Signal()
    change_profile_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("menuView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("menuBody")
        row = QHBoxLayout(body)
        row.setContentsMargins(24, 24, 24, 24)
        scroll.setWidget(body)
        layout.addWidget(scroll)
        card = QFrame()
        card.setProperty("panel", True)
        card.setMaximumWidth(500)
        content = QVBoxLayout(card)
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(10)
        title = QLabel("OBSIDIAN ROYALE")
        title.setObjectName("titleLabel")
        subtitle = QLabel("MENU GŁÓWNE")
        subtitle.setObjectName("subtitleLabel")
        self.player_label = QLabel()
        self.player_label.setObjectName("playerLabel")
        self.player_label.setTextFormat(Qt.TextFormat.PlainText)
        self.player_label.setWordWrap(True)
        self.balance_label = QLabel()
        self.balance_label.setObjectName("balanceLabel")
        self.balance_label.setTextFormat(Qt.TextFormat.PlainText)
        for widget in (title, subtitle, self.player_label, self.balance_label):
            content.addWidget(widget)
        self.game_button = QPushButton("Gra")
        self.game_button.setObjectName("gameButton")
        self.game_button.setProperty("variant", "primary")
        self.game_button.clicked.connect(self.game_requested)
        content.addWidget(self.game_button)
        self.statistics_button = QPushButton("Statystyki")
        self.statistics_button.setObjectName("statisticsButton")
        self.statistics_button.clicked.connect(self.statistics_requested)
        content.addWidget(self.statistics_button)
        for text in ("Sklep", "Ranking", "Ustawienia"):
            button = QPushButton(text)
            button.setEnabled(False)
            button.setToolTip("Niedostępne w tej wersji")
            content.addWidget(button)
        self.change_button = QPushButton("Zmień profil")
        self.change_button.setObjectName("changeProfileButton")
        self.exit_button = QPushButton("Wyjdź")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setProperty("variant", "danger")
        content.addWidget(self.change_button)
        content.addWidget(self.exit_button)
        row.addStretch()
        row.addWidget(card, 1, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        self.change_button.clicked.connect(self.change_profile_requested)
        self.exit_button.clicked.connect(self.exit_requested)

    def set_session(self, session):
        player = session.game.player
        self.player_label.setText(f"Gracz: {player.name}")
        self.balance_label.setText(f"Saldo: {player.balance}$")

    def set_blocked(self, blocked, reason=""):
        for button in (self.change_button, self.exit_button):
            button.setEnabled(not blocked)
            button.setToolTip(reason if blocked else "")
