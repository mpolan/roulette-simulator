from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                               QListWidget, QListWidgetItem, QLineEdit, QPushButton, QApplication)


def _label(text, role):
    label = QLabel(text)
    label.setProperty("role", role)
    label.setWordWrap(True)
    return label


def _panel():
    frame = QFrame()
    frame.setProperty("panel", True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(8)
    return frame, layout


class ProfilesView(QWidget):
    create_requested = Signal(str)
    select_requested = Signal(int)
    refresh_requested = Signal()
    back_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("profilesView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        title = QLabel("OBSIDIAN ROYALE")
        title.setObjectName("titleLabel")
        subtitle = QLabel("WYBIERZ GRACZA")
        subtitle.setObjectName("subtitleLabel")
        header = QVBoxLayout()
        header.setSpacing(3)
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)
        panels = QHBoxLayout()
        panels.setSpacing(12)
        existing, existing_layout = _panel()
        existing_layout.addWidget(_label("ISTNIEJĄCE PROFILE", "section"))
        existing_layout.addWidget(_label("Wybierz gracza z listy.", "hint"))
        self.profile_list = QListWidget()
        self.profile_list.setObjectName("profileList")
        self.profile_list.setAccessibleName("Dostępne profile graczy")
        self.profile_list.setMinimumHeight(154)
        self.profile_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        existing_layout.addWidget(self.profile_list, 1)
        self.select_button = QPushButton("Wybierz profil")
        self.select_button.setObjectName("selectProfileButton")
        self.select_button.setProperty("variant", "primary")
        existing_layout.addWidget(self.select_button)
        self.refresh_button = QPushButton("Odśwież listę")
        self.refresh_button.setObjectName("refreshProfilesButton")
        existing_layout.addWidget(self.refresh_button)
        create_panel, create_layout = _panel()
        create_layout.addWidget(_label("NOWY PROFIL", "section"))
        create_layout.addWidget(_label("Podaj nazwę gracza (maksymalnie 40 znaków).", "hint"))
        self.name_input = QLineEdit()
        self.name_input.setObjectName("profileName")
        self.name_input.setPlaceholderText("Nazwa gracza")
        self.name_input.setMaxLength(40)
        self.name_input.setAccessibleName("Nazwa gracza")
        create_layout.addWidget(self.name_input)
        self.create_button = QPushButton("Utwórz profil")
        self.create_button.setObjectName("createProfileButton")
        self.create_button.setProperty("variant", "primary")
        create_layout.addWidget(self.create_button)
        create_layout.addStretch()
        panels.addWidget(existing, 1)
        panels.addWidget(create_panel, 1)
        layout.addLayout(panels, 1)
        self.message = QLabel()
        self.message.setObjectName("profileMessage")
        self.message.setProperty("role", "error")
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(20)
        layout.addWidget(self.message)
        footer = QHBoxLayout()
        self.back_button = QPushButton("Powrót do menu")
        self.back_button.setObjectName("backToMenuButton")
        self.exit_button = QPushButton("Wyjdź")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setProperty("variant", "danger")
        footer.addWidget(self.back_button)
        footer.addStretch()
        footer.addWidget(self.exit_button)
        layout.addLayout(footer)
        self.profile_list.currentItemChanged.connect(self._selection_changed)
        self.profile_list.itemActivated.connect(lambda _: self._select())
        self.select_button.clicked.connect(self._select)
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.create_button.clicked.connect(self._create)
        self.name_input.returnPressed.connect(self._create)
        self.back_button.clicked.connect(self.back_requested)
        self.exit_button.clicked.connect(self.exit_requested)
        self._busy = False
        self._reason = ""
        self._focus_before_busy = None
        self._selection_changed()

    def _selection_changed(self, *_):
        selected = self.profile_list.currentItem() is not None
        self.select_button.setEnabled(not self._busy and selected)
        self.select_button.setToolTip(self._reason if self._busy else ("" if selected else "Wybierz profil z listy."))

    def _select(self):
        item = self.profile_list.currentItem()
        if item is not None:
            self.select_requested.emit(item.data(Qt.ItemDataRole.UserRole))

    def _create(self):
        self.create_requested.emit(self.name_input.text())

    def set_profiles(self, profiles):
        selected = self.profile_list.currentItem()
        selected_id = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        self.profile_list.clear()
        for profile in profiles:
            item = QListWidgetItem(f"{profile.name} — {profile.balance}$")
            item.setToolTip(f"{profile.name}\nSaldo: {profile.balance}$")
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self.profile_list.addItem(item)
            if profile.id == selected_id:
                self.profile_list.setCurrentItem(item)
        if profiles:
            if self.profile_list.currentItem() is None:
                self.profile_list.setCurrentRow(0)
            self.profile_list.setFocus()
        else:
            if not self.message.text():
                self.message.setText("Brak profili. Utwórz pierwszego gracza.")
            self.name_input.setFocus()
        self._selection_changed()

    def set_state(self, busy, has_session, blocked=False, reason="", back_blocked=False):
        was_busy = self._busy
        if busy and not was_busy:
            focused = QApplication.focusWidget()
            self._focus_before_busy = focused if focused is not None and self.isAncestorOf(focused) else None
        self._busy = busy or blocked
        self._reason = reason
        for widget in (self.profile_list, self.name_input, self.create_button, self.refresh_button):
            widget.setEnabled(not self._busy)
            widget.setToolTip(reason if self._busy else "")
        self.back_button.setEnabled(has_session and not back_blocked)
        self.back_button.setToolTip(reason if back_blocked else ("" if has_session else "Najpierw wybierz profil."))
        self.exit_button.setEnabled(not busy and not blocked)
        self.exit_button.setToolTip(reason if self._busy else "")
        self._selection_changed()
        if was_busy and not self._busy and self._focus_before_busy is not None:
            widget = self._focus_before_busy
            if self.isAncestorOf(widget) and widget.isEnabled():
                widget.setFocus()
            self._focus_before_busy = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.back_button.isEnabled():
            self.back_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)
