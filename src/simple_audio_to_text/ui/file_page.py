from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from simple_audio_to_text.services.audio_io import (
    AUDIO_FILE_SUFFIXES,
    duration_seconds,
    format_clock,
    is_supported_audio,
    media_filter,
)
from simple_audio_to_text.services.hub_progress import DownloadProgress
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.widgets import GhostButton, LoadStatusBar, PrimaryButton


class FilePage(QWidget):
    back = Signal()
    transcribe_requested = Signal(Path)
    copy_requested = Signal(str)
    save_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.path: Path | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 28, 40, 28)
        root.setSpacing(16)

        header = QHBoxLayout()
        self.back_btn = GhostButton("")
        self.back_btn.setFixedWidth(110)
        self.back_btn.clicked.connect(self.back.emit)
        self.title = QLabel()
        self.title.setProperty("pageTitle", True)
        header.addWidget(self.back_btn)
        header.addSpacing(12)
        header.addWidget(self.title)
        header.addStretch(1)

        self.drop = _DropZone()
        self.drop.clicked.connect(self._pick_file)
        self.drop.file_dropped.connect(self._set_file)

        self.meta = QLabel()
        self.meta.setProperty("muted", True)

        actions = QHBoxLayout()
        self.add_btn = PrimaryButton("")
        self.add_btn.clicked.connect(self._pick_file)
        self.run_btn = PrimaryButton("")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._request)
        actions.addWidget(self.add_btn)
        actions.addWidget(self.run_btn)
        actions.addStretch(1)

        self.load_bar = LoadStatusBar()
        self.status = QLabel("")
        self.status.setProperty("muted", True)

        self.result = QTextEdit()
        self.result.setMinimumHeight(220)

        export = QHBoxLayout()
        self.copy_btn = GhostButton("")
        self.save_btn = GhostButton("")
        self.copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.result.toPlainText()))
        self.save_btn.clicked.connect(lambda: self.save_requested.emit(self.result.toPlainText()))
        export.addWidget(self.copy_btn)
        export.addWidget(self.save_btn)
        export.addStretch(1)

        root.addLayout(header)
        root.addWidget(self.drop)
        root.addWidget(self.meta)
        root.addLayout(actions)
        root.addWidget(self.load_bar)
        root.addWidget(self.status)
        root.addWidget(self.result, 1)
        root.addLayout(export)
        self.retranslate()

    def retranslate(self) -> None:
        self.back_btn.setText(t("common.back"))
        self.title.setText(t("file.title"))
        self.add_btn.setText(t("file.add"))
        self.run_btn.setText(t("file.run"))
        self.copy_btn.setText(t("common.copy"))
        self.save_btn.setText(t("common.export"))
        self.result.setPlaceholderText(t("file.placeholder"))
        self.drop.set_prompt(t("file.drop"))
        if self.path is None:
            self.meta.setText(t("file.meta_empty"))

    def _pick_file(self) -> None:
        chosen, _ok = QFileDialog.getOpenFileName(
            self,
            t("file.pick"),
            "",
            media_filter(AUDIO_FILE_SUFFIXES, t("file.filter")),
        )
        if chosen:
            self._set_file(Path(chosen))

    def _set_file(self, path: Path) -> None:
        if not is_supported_audio(path):
            self.status.setText(t("file.bad_format"))
            return
        self.path = path
        length = duration_seconds(path)
        clock = format_clock(length) if length else "—"
        self.meta.setText(f"{path.name}  ·  {clock}")
        self.drop.set_label(path.name)
        self.run_btn.setEnabled(True)
        self.status.setText("")

    def _request(self) -> None:
        if self.path:
            self.transcribe_requested.emit(self.path)

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.run_btn.setEnabled(not busy and self.path is not None)
        if busy:
            self.status.setText("")
            if message:
                self.load_bar.apply(DownloadProgress(percent=None, message=message))
        else:
            self.load_bar.apply(None)
            self.status.setText(message)

    def set_load_progress(self, progress: DownloadProgress | None) -> None:
        self.status.setText("")
        self.load_bar.apply(progress)

    def set_text(self, text: str) -> None:
        self.result.setPlainText(text)


class _DropZone(QFrame):
    clicked = Signal()
    file_dropped = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("drop")
        self.setMinimumHeight(150)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        self._prompt = ""
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setProperty("muted", True)
        layout.addWidget(self.label)

    def set_prompt(self, text: str) -> None:
        showing_prompt = self.label.text() == self._prompt or not self.label.text()
        self._prompt = text
        if showing_prompt:
            self.label.setText(text)

    def set_label(self, text: str) -> None:
        self.label.setText(text)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.exists():
                self.file_dropped.emit(path)
                break
