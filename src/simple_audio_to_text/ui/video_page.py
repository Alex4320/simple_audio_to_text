from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from simple_audio_to_text.services.audio_io import (
    VIDEO_FILE_SUFFIXES,
    duration_seconds,
    format_clock,
    is_supported_video,
    media_filter,
)
from simple_audio_to_text.services.hub_progress import DownloadProgress
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.file_page import _DropZone
from simple_audio_to_text.ui.widgets import GhostButton, LoadStatusBar, PrimaryButton


class VideoPage(QWidget):
    back = Signal()
    convert_requested = Signal(Path, bool)
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

        self.transcribe_box = QCheckBox()

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
        self.result.setMinimumHeight(180)

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
        root.addWidget(self.transcribe_box)
        root.addLayout(actions)
        root.addWidget(self.load_bar)
        root.addWidget(self.status)
        root.addWidget(self.result, 1)
        root.addLayout(export)
        self.retranslate()

    def retranslate(self) -> None:
        self.back_btn.setText(t("common.back"))
        self.title.setText(t("video.title"))
        self.add_btn.setText(t("video.add"))
        self.run_btn.setText(t("video.run"))
        self.copy_btn.setText(t("video.copy"))
        self.save_btn.setText(t("video.export"))
        self.transcribe_box.setText(t("video.transcribe"))
        self.transcribe_box.setToolTip(t("video.transcribe_tip"))
        self.result.setPlaceholderText(t("video.placeholder"))
        self.drop.set_prompt(t("video.drop"))
        if self.path is None:
            self.meta.setText(t("video.meta_empty"))

    def _pick_file(self) -> None:
        chosen, _ok = QFileDialog.getOpenFileName(
            self,
            t("video.pick"),
            "",
            media_filter(VIDEO_FILE_SUFFIXES, t("video.filter")),
        )
        if chosen:
            self._set_file(Path(chosen))

    def _set_file(self, path: Path) -> None:
        if not is_supported_video(path):
            self.status.setText(t("video.bad_format"))
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
            self.convert_requested.emit(self.path, self.transcribe_box.isChecked())

    def wants_transcript(self) -> bool:
        return self.transcribe_box.isChecked()

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.run_btn.setEnabled(not busy and self.path is not None)
        self.transcribe_box.setEnabled(not busy)
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
