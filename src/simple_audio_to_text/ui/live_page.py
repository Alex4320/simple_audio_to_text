from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from simple_audio_to_text.services.devices import AudioSource, refresh_sources
from simple_audio_to_text.services.hub_progress import DownloadProgress
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.widgets import GhostButton, LevelMeter, LoadStatusBar, PrimaryButton, RecBadge


class LivePage(QWidget):
    back = Signal()
    start_requested = Signal(object)
    pause_requested = Signal(bool)
    stop_requested = Signal()
    copy_requested = Signal(str)
    save_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._paused = False
        self._running = False
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
        self.load_bar = LoadStatusBar()
        self.meter = LevelMeter()
        self.meter.setFixedHeight(14)
        self.status = QLabel()
        self.status.setProperty("muted", True)

        controls = QHBoxLayout()
        self.start_btn = PrimaryButton("")
        self.pause_btn = GhostButton("")
        self.pause_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._toggle_run)
        self.pause_btn.clicked.connect(self._toggle_pause)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.pause_btn)
        controls.addStretch(1)

        self.result = QTextEdit()

        export = QHBoxLayout()
        self.copy_btn = GhostButton("")
        self.save_btn = GhostButton("")
        self.copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.result.toPlainText()))
        self.save_btn.clicked.connect(lambda: self.save_requested.emit(self.result.toPlainText()))
        export.addWidget(self.copy_btn)
        export.addWidget(self.save_btn)
        export.addStretch(1)

        root.addLayout(header)
        root.addWidget(self.rec_banner)
        root.addWidget(self.load_bar)
        root.addLayout(columns, 1)
        root.addWidget(self.meter)
        root.addWidget(self.status)
        root.addLayout(controls)
        root.addWidget(self.result, 2)
        root.addLayout(export)
        self.retranslate()
        self.reload_sources()

    def retranslate(self) -> None:
        self.back_btn.setText(t("common.back"))
        self.title.setText(t("live.title"))
        self.refresh_btn.setText(t("common.refresh"))
        self.mic_heading.setText(t("common.mic"))
        self.app_heading.setText(t("common.app"))
        self.copy_btn.setText(t("common.copy"))
        self.save_btn.setText(t("common.export"))
        self.result.setPlaceholderText(t("live.placeholder"))
        self._restyle_run_button()
        self.pause_btn.setText(t("common.resume") if self._paused else t("common.pause"))
        if self._running:
            self.rec_banner.setText(t("common.pause") if self._paused else t("common.recording_level"))
        else:
            self.status.setText(t("live.status"))

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
            self.status.setText(t("live.need_source"))
            return
        self.start_requested.emit(source)

    def _restyle_run_button(self) -> None:
        if self._running:
            self.start_btn.setText(t("common.stop"))
            self.start_btn.setProperty("primary", False)
            self.start_btn.setProperty("danger", True)
        else:
            self.start_btn.setText(t("common.start"))
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
        self._restyle_run_button()
        self.pause_btn.setEnabled(running)
        self.mic_list.setEnabled(not running)
        self.app_list.setEnabled(not running)
        if running:
            self.rec.stop()
            self.rec_banner.hide()
        else:
            self._paused = False
            self.pause_btn.setText(t("common.pause"))
            self.meter.set_level(0)
            self.rec.stop()
            self.rec_banner.hide()
            self.load_bar.apply(None)

    def set_load_progress(self, progress: DownloadProgress | None) -> None:
        if progress is None:
            self.load_bar.apply(None)
            if self._running and not self.rec.isVisible():
                self.rec.start()
                self.rec_banner.setText(t("common.recording_level"))
                self.rec_banner.show()
            return
        self.load_bar.apply(progress)

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def set_level(self, value: float) -> None:
        self.meter.set_level(value)

    def set_text(self, text: str) -> None:
        self.result.setPlainText(text)
        cursor = self.result.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.result.setTextCursor(cursor)
