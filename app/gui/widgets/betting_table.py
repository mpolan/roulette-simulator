"""Europejski układ stołu z trwałymi polami QGraphicsScene."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsObject, QGraphicsScene, QGraphicsView, QSizePolicy

from domain.bet import BetType
from gui.widgets.chip_picker import CHIP_COLORS


class _Field(QGraphicsObject):
    def __init__(self, owner, key, label, rect, color):
        super().__init__()
        self.owner = owner
        self.key = key
        self.label = label
        self.rect = QRectF(0, 0, rect.width(), rect.height())
        self.setPos(rect.topLeft())
        self.color = color
        self.stack = ()
        self.total = 0
        self.selected = False
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_data((), 0, False, 5)

    def boundingRect(self):
        return self.rect

    def update_data(self, stack, total, selected, limit):
        snapshot = (tuple(id(bet) for bet in stack), total, selected, limit)
        if getattr(self, "_snapshot", None) == snapshot:
            return False
        self._snapshot = snapshot
        self.stack, self.total, self.selected = tuple(stack), total, selected
        self.setToolTip(f"{self.label} · stawka {total}$ · żetony {len(stack)}/{limit}\n"
                        "CHIPS: lewy klik / Enter dodaje; prawy klik / Delete usuwa ostatni.\n"
                        "CLASSIC: klik zaznacza pole, następnie zatwierdź stawkę.")
        self.update()
        return True

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.color)
        if self.hovered:
            color = color.lighter(130)
        painter.setBrush(color)
        focused = self.owner.hasFocus() and self.owner.focus_key == self.key
        painter.setPen(QPen(QColor("#F5D58C" if self.selected or focused else "#94A591"),
                            3 if self.selected or focused else 1))
        painter.drawRoundedRect(self.rect.adjusted(2, 2, -2, -2), 4, 4)
        painter.setPen(QColor("#F5D58C" if self.selected else "#F0EDE5"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        label_rect = self.rect.adjusted(3, 5, -3, -5)
        if self.stack or self.total:
            label_rect.setHeight(self.rect.height() * 0.46)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.label)
        if self.stack:
            # Każdy krążek odpowiada jednemu Bet w publicznym chip_stacks.
            diameter = 11
            width = len(self.stack) * 10 + 1
            start = (self.rect.width() - width) / 2
            y = self.rect.height() * 0.48
            for index, bet in enumerate(self.stack):
                painter.setBrush(QColor(CHIP_COLORS.get(bet.amount, "#F5D58C")))
                painter.setPen(QPen(QColor("#F0EDE5"), 0.8))
                painter.drawEllipse(QRectF(start + index * 10, y, diameter, diameter))
        if self.total:
            painter.setPen(QColor("#F5D58C"))
            font = QFont("Segoe UI")
            font.setPixelSize(13)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect.adjusted(3, self.rect.height() - 19, -3, -2),
                             Qt.AlignmentFlag.AlignCenter, f"{self.total}$")

    def mousePressEvent(self, event):
        if self.owner.isEnabled():
            self.owner.setFocus(Qt.FocusReason.MouseFocusReason)
            self.owner.set_focus_key(self.key)
            self.owner.field_activated.emit(self.key[0], self.key[1],
                                            event.button() == Qt.MouseButton.RightButton)
        event.accept()

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()


class BettingTable(QGraphicsView):
    field_activated = Signal(object, object, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("Europejski stół ruletki. Strzałki wybierają pole, Enter stawia, Delete usuwa.")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QGraphicsView { background: #10271E; border: 1px solid #A58B58; border-radius: 6px; }")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(198)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.setSceneRect(0, 0, 920, 296)
        self.fields = {}
        self.focus_key = (BetType.STRAIGHT, 0)
        self._pocket_colors = None
        self._build()

    def _add(self, kind, selection, label, rect, color="#174432"):
        key = (kind, selection)
        item = _Field(self, key, label, QRectF(*rect), color)
        self.fields[key] = item
        self._scene.addItem(item)

    def _build(self):
        self._add(BetType.STRAIGHT, 0, "0", (0, 0, 58, 192))
        for row, start in enumerate((3, 2, 1)):
            for column, number in enumerate(range(start, 37, 3)):
                self._add(BetType.STRAIGHT, number, str(number),
                          (58 + column * 66, row * 64, 66, 64), "#15212A")
            self._add(BetType.COLUMN, start, f"KOL {start}", (850, row * 64, 70, 64))
        for dozen in (1, 2, 3):
            lower, upper = (dozen - 1) * 12 + 1, dozen * 12
            self._add(BetType.DOZEN, dozen, f"{lower}–{upper}",
                      (58 + (dozen - 1) * 264, 192, 264, 52))
        outside = ((BetType.LOW, "1–18"), (BetType.EVEN, "PARZYSTE"),
                   (BetType.RED, "CZERWONE"), (BetType.BLACK, "CZARNE"),
                   (BetType.ODD, "NIEPARZ."), (BetType.HIGH, "19–36"))
        for index, (kind, label) in enumerate(outside):
            color = "#8C2939" if kind == BetType.RED else "#15212A" if kind == BetType.BLACK else "#174432"
            self._add(kind, None, label, (58 + index * 132, 244, 132, 52), color)

    def set_pockets(self, pockets):
        colors = tuple((p.number, p.color.value) for p in pockets)
        if colors == self._pocket_colors:
            return
        self._pocket_colors = colors
        palette = {"green": "#176641", "red": "#8C2939", "black": "#15212A"}
        for number, color in colors:
            field = self.fields[(BetType.STRAIGHT, number)]
            field.color = palette[color]
            field.update()

    def update_fields(self, game, selected_numbers=(), outside=None):
        stacks = game.chip_stacks
        totals = {}
        for bet in game.current_bets:
            key = (bet.bet_type, bet.selection)
            totals[key] = totals.get(key, 0) + bet.amount
        changed = []
        for key, field in self.fields.items():
            selected = key == outside or (key[0] == BetType.STRAIGHT and key[1] in selected_numbers)
            if field.update_data(stacks.get(key, ()), totals.get(key, 0), selected,
                                 game.MAX_CHIPS_PER_FIELD):
                changed.append(key)
        return changed

    def set_focus_key(self, key):
        if key == self.focus_key:
            return
        old_key = self.focus_key
        self.focus_key = key
        self.fields[old_key].update()
        self.fields[key].update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.fields[self.focus_key].update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.fields[self.focus_key].update()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space,
                   Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            remove = key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)
            self.field_activated.emit(*self.focus_key, remove)
            event.accept()
            return
        directions = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                      Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if key in directions:
            dx, dy = directions[key]
            center = self.fields[self.focus_key].sceneBoundingRect().center()
            candidates = []
            for field_key, field in self.fields.items():
                delta = field.sceneBoundingRect().center() - center
                forward = delta.x() * dx + delta.y() * dy
                cross = abs(delta.y() * dx - delta.x() * dy)
                if forward > 1:
                    candidates.append((forward + cross * 4, field_key))
            if candidates:
                self.set_focus_key(min(candidates, key=lambda item: item[0])[1])
            event.accept()
            return
        super().keyPressEvent(event)
