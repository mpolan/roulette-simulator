"""Koło prezentacji: geometria z Wheel, animacja wyłącznie do RoundResult."""

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QSizePolicy, QWidget


POCKET_COLORS = {"red": "#A52F43", "black": "#14212D", "green": "#20734E"}


class RouletteWheel(QWidget):
    animation_finished = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pockets = ()
        self.rotation = 0.0
        self.result = None
        self.animating = False
        self.duration_ms = 4200
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("Europejskie koło ruletki")
        self.animation = QVariantAnimation(self)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self._rotate)
        self.animation.finished.connect(self._finish)

    def set_pockets(self, pockets):
        pockets = tuple(pockets)
        if pockets != self.pockets:
            self.pockets = pockets
            self.reset()

    def reset(self):
        self.animation.stop()
        self.animating = False
        self.result = None
        self.rotation = 0.0
        self.update()

    def target_rotation(self, pocket):
        index = self.pockets.index(pocket)
        return (-index * 360.0 / len(self.pockets)) % 360.0

    def number_at_pointer(self):
        if not self.pockets:
            return None
        index = round((-self.rotation % 360.0) / (360.0 / len(self.pockets))) % len(self.pockets)
        return self.pockets[index].number

    def start(self, result):
        if self.animating:
            return
        target = self.target_rotation(result.pocket)
        self.result = result
        self.animating = True
        start = self.rotation % 360.0
        self.animation.setDuration(self.duration_ms)
        self.animation.setStartValue(start)
        self.animation.setEndValue(start + 5 * 360.0 + (target - start) % 360.0)
        self.animation.start()

    def _rotate(self, value):
        self.rotation = float(value)
        self.update()

    def _finish(self):
        if not self.animating:
            return
        self.rotation = self.target_rotation(self.result.pocket)
        self.animating = False
        self.update()
        self.animation_finished.emit(self.result)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        scale = min(self.width(), self.height()) / 490.0
        painter.scale(scale, scale)
        painter.setBrush(QColor("#111D27"))
        painter.setPen(QPen(QColor("#A58B58"), 5))
        painter.drawEllipse(QRectF(-222, -222, 444, 444))
        if not self.pockets:
            return
        painter.save()
        painter.rotate(self.rotation)
        step = 360.0 / len(self.pockets)
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        for index, pocket in enumerate(self.pockets):
            painter.setBrush(QColor(POCKET_COLORS[pocket.color.value]))
            painter.setPen(QPen(QColor("#C8B27A"), 0.9))
            painter.drawPie(QRectF(-210, -210, 420, 420),
                            round((90 + step / 2 - index * step) * 16), round(-step * 16))
            painter.save()
            painter.rotate(index * step)
            painter.setPen(QColor("#FFF7E5"))
            painter.drawText(QRectF(-18, -204, 36, 36), Qt.AlignmentFlag.AlignCenter, str(pocket.number))
            painter.restore()
        painter.restore()
        painter.setBrush(QColor("#18362D"))
        painter.setPen(QPen(QColor("#A58B58"), 3))
        painter.drawEllipse(QRectF(-151, -151, 302, 302))
        painter.setBrush(QColor("#0C151E"))
        painter.setPen(QPen(QColor("#5C5139"), 2))
        painter.drawEllipse(QRectF(-103, -103, 206, 206))
        painter.setPen(QColor("#F5D58C"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.drawText(QRectF(-130, -65, 260, 30), Qt.AlignmentFlag.AlignCenter, "OBSIDIAN ROYALE")
        painter.setFont(QFont("Segoe UI", 40, QFont.Weight.Bold))
        text = "· · ·" if self.animating else str(self.result.pocket.number) if self.result else "0–36"
        painter.drawText(QRectF(-100, -30, 200, 80), Qt.AlignmentFlag.AlignCenter, text)
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor("#B8C6C0"))
        painter.drawText(QRectF(-130, 53, 260, 26), Qt.AlignmentFlag.AlignCenter,
                         "KOŁO W RUCHU" if self.animating else "RULETKA EUROPEJSKA")
        # Nieruchomy wskaźnik celuje w środek sektora na godzinie 12.
        painter.setBrush(QColor("#F5D58C"))
        painter.setPen(QPen(QColor("#080D14"), 2))
        painter.drawPolygon(QPolygonF([QPointF(-13, -234), QPointF(13, -234), QPointF(0, -202)]))
