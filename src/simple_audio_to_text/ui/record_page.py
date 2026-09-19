from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from simple_audio_to_text.services.audio_export import join_takes
from simple_audio_to_text.services.audio_io import RECORD_RATE, format_clock
from simple_audio_to_text.services.devices import AudioSource, refresh_sources
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.widgets import GhostButton, LevelMeter, PrimaryButton, RecBadge


class RecordPage(QWidget):
    back = Signal()
    start_requested = Signal(object)
    pause_requested = Signal(bool)
    stop_requested = Signal()
    export_requested = Signal()
    clear_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._paused = False
        self._running = False
        self._takes: list[np.ndarray] = []
        self._live_seconds = 0.0
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
        self.rec = RecBadge()
        header.addWidget(self.rec)
        self.refresh_btn = GhostButton("")
        self.refresh_btn.clicked.connect(self.reload_sources)
        header.addWidget(self.refresh_btn)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        self.mic_list = QListWidget()
        self.app_list = QListWidget()
        self.mic_list.itemClicked.connect(self._choose_mic)
        self.app_list.itemClicked.connect(self._choose_app)
        self.mic_heading = QLabel()
        self.app_heading = QLabel()
        columns.addWidget(self._wrap_list(self.mic_heading, self.mic_list))
        columns.addWidget(self._wrap_list(self.app_heading, self.app_list))

        self.rec_banner = QLabel()
        self.rec_banner.setObjectName("recBanner")
        self.rec_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rec_banner.hide()

        self.clock = QLabel("00:00")
        self.clock.setProperty("pageTitle", True)
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meta = QLabel()
        self.meta.setProperty("muted", True)
        self.meta.setWordWrap(True)
        self.meta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.meter = LevelMeter()
        self.meter.setFixedHeight(14)
        self.status = QLabel()
        self.status.setProperty("muted", True)

        controls = QHBoxLayout()
        self.start_btn = PrimaryButton("")
        self.pause_btn = GhostButton("")
        self.clear_btn = GhostButton("")
        self.export_btn = GhostButton("")
        self.pause_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._toggle_run)
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        self.export_btn.clicked.connect(self.export_requested.emit)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.clear_btn)
        controls.addWidget(self.export_btn)
        controls.addStretch(1)

        root.addLayout(header)
        root.addWidget(self.rec_banner)
        root.addLayout(columns, 1)
        root.addWidget(self.clock)
        root.addWidget(self.meta)
        root.addWidget(self.meter)
        root.addWidget(self.status)
        root.addLayout(controls)
        self.retranslate()
        self.reload_sources()
        self._refresh_session()

    def retranslate(self) -> None:
        self.back_btn.setText(t("common.back"))
        self.title.setText(t("record.title"))
        self.refresh_btn.setText(t("common.refresh"))
        self.mic_heading.setText(t("common.mic"))
        self.app_heading.setText(t("common.device_app"))
        self.clear_btn.setText(t("record.new"))
        self.export_btn.setText(t("common.export"))
        self.pause_btn.setText(t("common.resume") if self._paused else t("common.pause"))
        if self._running:
            self.rec_banner.setText(t("common.pause") if self._paused else t("common.recording_level"))
        if not self._running and not self._takes:
            self.status.setText(t("record.status"))
        self._refresh_session()

    def _wrap_list(self, label: QLabel, widget: QListWidget) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)
        layout.addWidget(widget)
        return box

    def reload_sources(self) -> None:
        selected = self.selected_source()
        mics, apps = refresh_sources()
        self._fill(self.mic_list, mics)
        self._fill(self.app_list, apps)
        if selected is not None:
            self._restore_selection(selected)

    def _fill(self, widget: QListWidget, sources: list[AudioSource]) -> None:
        widget.clear()
        for source in sources:
            label = source.title if source.kind == "app" or not source.detail else f"{source.title}  ·  {source.detail}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, source)
            widget.addItem(item)

    def _choose_mic(self, item: QListWidgetItem) -> None:
        self.app_list.blockSignals(True)
        self.app_list.clearSelection()
        self.app_list.blockSignals(False)
        self.mic_list.setCurrentItem(item)

    def _choose_app(self, item: QListWidgetItem) -> None:
        self.mic_list.blockSignals(True)
        self.mic_list.clearSelection()
        self.mic_list.blockSignals(False)
        self.app_list.setCurrentItem(item)

    def _restore_selection(self, source: AudioSource) -> None:
        widget = self.mic_list if source.kind == "mic" else self.app_list
        for row in range(widget.count()):
            item = widget.item(row)
            stored = item.data(Qt.ItemDataRole.UserRole)
            if stored and stored.key == source.key:
                if source.kind == "mic":
                    self._choose_mic(item)
                else:
                    self._choose_app(item)
                return

    def selected_source(self) -> AudioSource | None:
        for widget in (self.app_list, self.mic_list):
            item = widget.currentItem()
            if item is not None and item.isSelected():
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _toggle_run(self) -> None:
        if self._running:
            self.stop_requested.emit()
            return
        source = self.selected_source()
        if source is None:
            self.status.setText(t("record.need_source"))
            return
        self.start_requested.emit(source)

    def _restyle_run_button(self) -> None:
        if self._running:
            self.start_btn.setText(t("common.stop"))
            self.start_btn.setProperty("primary", False)
            self.start_btn.setProperty("danger", True)
        else:
            self.start_btn.setText(t("common.resume") if self._takes else t("common.start"))
            self.start_btn.setProperty("primary", True)
            self.start_btn.setProperty("danger", False)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self.pause_btn.setText(t("common.resume") if self._paused else t("common.pause"))
        self.rec.set_paused(self._paused)
        self.rec_banner.setText(t("common.pause") if self._paused else t("common.recording_level"))
        self.pause_requested.emit(self._paused)

    def set_running(self, running: bool) -> None:
        self._running = running
        if not running:
            self._live_seconds = 0.0
            self._paused = False
            self.pause_btn.setText(t("common.pause"))
            self.meter.set_level(0)
            self.rec.stop()
            self.rec_banner.hide()
        else:
            self.rec.start()
            self.rec_banner.setText(t("common.recording_level"))
            self.rec_banner.show()
        self.pause_btn.setEnabled(running)
        self.mic_list.setEnabled(not running)
        self.app_list.setEnabled(not running)
        self._refresh_session()

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def set_level(self, value: float) -> None:
        self.meter.set_level(value)

    def set_live_seconds(self, seconds: float) -> None:
        self._live_seconds = max(0.0, seconds)
        self._refresh_session()

    def append_take(self, audio: np.ndarray) -> None:
        chunk = np.ascontiguousarray(audio, dtype=np.float32).reshape(-1)
        if chunk.size:
            self._takes.append(chunk)
        self._live_seconds = 0.0
        self._refresh_session()

    def clear_takes(self) -> None:
        self._takes = []
        self._live_seconds = 0.0
        self._refresh_session()

    def combined_audio(self) -> np.ndarray:
        return join_takes(self._takes)

    def has_audio(self) -> bool:
        return any(item.size for item in self._takes)

    def _saved_seconds(self) -> float:
        return sum(item.size for item in self._takes) / RECORD_RATE

    def _refresh_session(self) -> None:
        total = self._saved_seconds() + self._live_seconds
        self.clock.setText(format_clock(total))
        count = len(self._takes)
        if self._running:
            extra = t("record.meta_running_extra") if count else ""
            self.meta.setText(t("record.meta_running", count=count, extra=extra))
        elif count:
            self.meta.setText(t("record.meta_ready", count=count, clock=format_clock(self._saved_seconds())))
        else:
            self.meta.setText(t("record.meta_empty"))
        can_use = self.has_audio() and not self._running
        self.clear_btn.setEnabled(can_use)
        self.export_btn.setEnabled(can_use)
        self._restyle_run_button()
