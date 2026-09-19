from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from simple_audio_to_text.services.hub_progress import DownloadProgress
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.theme import ACCENT, BG, DANGER, LINE, MUTED, SURFACE, SURFACE_2, TEXT


class Switch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(48, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self.update()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 4, 46, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACCENT if self._checked else LINE))
        painter.drawRoundedRect(track, 10, 10)
        knob_x = 26 if self._checked else 4
        painter.setBrush(QColor(BG if self._checked else TEXT))
        painter.drawEllipse(QRectF(knob_x, 6, 16, 16))


class IconButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("iconish", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class GearButton(IconButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self.setToolTip(t("common.settings"))

    def retranslate(self) -> None:
        self.setToolTip(t("common.settings"))

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(TEXT))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        center = self.rect().center()
        painter.drawEllipse(center, 7, 7)
        painter.drawEllipse(center, 3, 3)
        for angle in range(0, 360, 45):
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.drawLine(0, -10, 0, -7)
            painter.restore()


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("primary", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)


class GhostButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)


CARD_HEIGHT = 260


class ModeCard(QFrame):
    clicked = Signal()

    def __init__(
        self,
        kind: str,
        title: str,
        subtitle: str,
        parent: QWidget | None = None,
        compact: bool = False,
    ) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setObjectName("modeCardMini" if compact else "modeCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.title_label = QLabel(title)
        self.title_label.setProperty("cardTitleMini" if compact else "cardTitle", True)
        self.title_label.setWordWrap(False)
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("muted", True)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.subtitle_label.setFixedHeight(36)
        if compact:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(14)
            texts = QVBoxLayout()
            texts.setContentsMargins(0, 0, 0, 0)
            texts.setSpacing(4)
            texts.addWidget(self.title_label)
            texts.addWidget(self.subtitle_label)
            texts.addStretch(1)
            layout.addWidget(_Glyph(kind, 40), 0, Qt.AlignmentFlag.AlignTop)
            layout.addLayout(texts, 1)
        else:
            self.setFixedHeight(CARD_HEIGHT)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(12)
            layout.addWidget(_Glyph(kind, 48), 0, Qt.AlignmentFlag.AlignLeft)
            layout.addSpacing(8)
            layout.addWidget(self.title_label)
            layout.addWidget(self.subtitle_label)
            layout.addStretch(1)

    def set_texts(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ModeStack(QFrame):
    def __init__(self, *cards: ModeCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("modeStack")
        self.setFixedHeight(CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for index, card in enumerate(cards):
            if index:
                line = QFrame()
                line.setObjectName("modeSplit")
                line.setFixedHeight(1)
                layout.addWidget(line)
            layout.addWidget(card, 1)


class _Glyph(QWidget):
    def __init__(self, kind: str, size: int = 56) -> None:
        super().__init__()
        self.kind = kind
        self.setFixedSize(size, size)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = self.width() / 56
        painter.scale(scale, scale)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SURFACE_2))
        painter.drawRoundedRect(QRectF(0, 0, 56, 56), 16, 16)
        pen = QPen(QColor(ACCENT))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.kind == "file":
            path = QPainterPath()
            path.moveTo(18, 14)
            path.lineTo(32, 14)
            path.lineTo(40, 22)
            path.lineTo(40, 42)
            path.lineTo(16, 42)
            path.lineTo(16, 14)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(32, 14, 32, 22)
            painter.drawLine(32, 22, 40, 22)
            painter.drawLine(22, 28, 34, 28)
            painter.drawLine(22, 34, 30, 34)
            return
        if self.kind == "save":
            painter.drawRoundedRect(QRectF(16, 14, 24, 18), 4, 4)
            painter.setBrush(QColor(ACCENT))
            painter.drawEllipse(QRectF(24, 18, 8, 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(28, 32, 28, 42)
            painter.drawLine(22, 38, 28, 44)
            painter.drawLine(34, 38, 28, 44)
            return
        if self.kind == "video":
            painter.drawRoundedRect(QRectF(14, 16, 28, 24), 5, 5)
            play = QPainterPath()
            play.moveTo(24, 22)
            play.lineTo(34, 28)
            play.lineTo(24, 34)
            play.closeSubpath()
            painter.drawPath(play)
            return
        painter.drawEllipse(QPoint(20, 28), 6, 6)
        painter.drawLine(20, 22, 20, 38)
        painter.drawLine(26, 28, 42, 28)
        for index, height in enumerate((8, 14, 10, 16, 7)):
            x = 28 + index * 4
            painter.drawLine(x, 28 - height // 2, x, 28 + height // 2)


class RecBadge(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = "idle"
        self._pulse_on = True
        self._elapsed = 0
        self._pulse = QTimer(self)
        self._pulse.timeout.connect(self._blink)
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick)
        self.setFixedHeight(34)
        self.setMinimumWidth(168)
        self.hide()

    def start(self) -> None:
        self._state = "rec"
        self._elapsed = 0
        self._pulse_on = True
        self._pulse.start(450)
        self._clock.start(1000)
        self.show()
        self.update()

    def set_paused(self, paused: bool) -> None:
        self._state = "pause" if paused else "rec"
        if paused:
            self._clock.stop()
            self._pulse.stop()
            self._pulse_on = True
        else:
            self._pulse.start(450)
            self._clock.start(1000)
        self.update()

    def stop(self) -> None:
        self._state = "idle"
        self._pulse.stop()
        self._clock.stop()
        self.hide()

    def _blink(self) -> None:
        self._pulse_on = not self._pulse_on
        self.update()

    def _tick(self) -> None:
        self._elapsed += 1
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(DANGER))
        painter.drawRoundedRect(self.rect(), 17, 17)
        minutes, seconds = divmod(self._elapsed, 60)
        hours, minutes = divmod(minutes, 60)
        clock = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        label = f"{t('badge.pause')}  {clock}" if self._state == "pause" else f"REC  {clock}"
        if self._state == "rec" and self._pulse_on:
            painter.setBrush(QColor(TEXT))
            painter.drawEllipse(QRectF(12, 11, 12, 12))
        elif self._state == "pause":
            painter.setBrush(QColor(BG))
            painter.drawRoundedRect(QRectF(12, 11, 5, 12), 1, 1)
            painter.drawRoundedRect(QRectF(20, 11, 5, 12), 1, 1)
        painter.setPen(QColor(TEXT))
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(QRect(36, 0, self.width() - 44, self.height()), Qt.AlignmentFlag.AlignVCenter, label)


class LevelMeter(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._level = 0.0
        self.setFixedHeight(10)

    def set_level(self, value: float) -> None:
        self._level = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SURFACE_2))
        painter.drawRoundedRect(self.rect(), 5, 5)
        width = max(8, int(self.width() * self._level))
        painter.setBrush(QColor(ACCENT))
        painter.drawRoundedRect(QRect(0, 0, width, self.height()), 5, 5)


class LoadStatusBar(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("loadStatus")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        self.bar = QProgressBar()
        self.bar.setObjectName("loadBar")
        self.bar.setTextVisible(True)
        self.bar.setMinimumHeight(18)
        self.detail = QLabel("")
        self.detail.setProperty("muted", True)
        self.detail.setWordWrap(True)
        layout.addWidget(self.bar)
        layout.addWidget(self.detail)
        self.hide()

    def apply(self, progress: DownloadProgress | None) -> None:
        if progress is None:
            self.hide()
            return
        self.show()
        if progress.percent is None:
            self.bar.setRange(0, 0)
            self.bar.setFormat("")
        else:
            self.bar.setRange(0, 100)
            self.bar.setValue(progress.percent)
            self.bar.setFormat(f"{progress.percent}%")
        self.detail.setText(progress.message)


class SettingRow(QFrame):
    def __init__(self, title: str, subtitle: str, control: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        self.head = QLabel(title)
        self.head.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.sub = QLabel(subtitle)
        self.sub.setProperty("muted", True)
        self.sub.setWordWrap(True)
        texts.addWidget(self.head)
        texts.addWidget(self.sub)
        layout.addLayout(texts, 1)
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_texts(self, title: str, subtitle: str) -> None:
        self.head.setText(title)
        self.sub.setText(subtitle)
