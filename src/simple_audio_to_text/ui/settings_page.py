from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from simple_audio_to_text.services.asr import describe_compute, list_cuda_devices
from simple_audio_to_text.services.i18n import UI_LANGUAGES, set_ui_language, t
from simple_audio_to_text.services.settings import (
    DEVICES,
    LANGUAGES,
    MODELS,
    AppSettings,
    model_memory,
    model_memory_text,
)
from simple_audio_to_text.ui.widgets import GhostButton, SettingRow, Switch

_SWITCH_ROWS = (
    ("remove_fillers", "settings.fillers", "settings.fillers_sub"),
    ("split_speakers", "settings.speakers", "settings.speakers_sub"),
    ("denoise", "settings.denoise", "settings.denoise_sub"),
    ("remove_silence", "settings.silence", "settings.silence_sub"),
    ("normalize", "settings.normalize", "settings.normalize_sub"),
    ("timestamps", "settings.timestamps", "settings.timestamps_sub"),
)


class SettingsPage(QWidget):
    back = Signal()
    changed = Signal(object)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self._gpus = list_cuda_devices()
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 28, 40, 28)
        root.setSpacing(14)

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
        root.addLayout(header)

        self.hint = QLabel()
        self.hint.setProperty("muted", True)
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

        self.ui_language_box = QComboBox()
        self.model_box = QComboBox()
        self.language_box = QComboBox()
        self.device_box = QComboBox()
        self.gpu_box = QComboBox()

        self.model_status = QLabel()
        self.model_status.setWordWrap(True)
        self.gpu_status = QLabel()
        self.gpu_status.setWordWrap(True)
        self.gpu_status.setProperty("muted", True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setContentsMargins(0, 0, 8, 0)
        form.setSpacing(12)
        self.ui_row = SettingRow("", "", self.ui_language_box)
        self.model_row = SettingRow("", "", self.model_box)
        self.speech_row = SettingRow("", "", self.language_box)
        self.device_row = SettingRow("", "", self.device_box)
        self.gpu_row = SettingRow("", "", self.gpu_box)
        form.addWidget(self.ui_row)
        form.addWidget(self.model_row)
        form.addWidget(self.model_status)
        form.addWidget(self.speech_row)
        form.addWidget(self.device_row)
        form.addWidget(self.gpu_row)
        form.addWidget(self.gpu_status)

        self.switches = {
            "remove_fillers": Switch(settings.remove_fillers),
            "split_speakers": Switch(settings.split_speakers),
            "denoise": Switch(settings.denoise),
            "remove_silence": Switch(settings.remove_silence),
            "normalize": Switch(settings.normalize),
            "timestamps": Switch(settings.timestamps),
        }
        self.switch_rows: dict[str, SettingRow] = {}
        for key, title_key, subtitle_key in _SWITCH_ROWS:
            switch = self.switches[key]
            switch.toggled.connect(lambda _checked, _k=key: self._emit())
            row = SettingRow("", "", switch)
            self.switch_rows[key] = row
            form.addWidget(row)
        form.addStretch(1)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        self.retranslate()
        self._select_gpu(settings.gpu_index)
        self.ui_language_box.currentIndexChanged.connect(self._emit)
        self.model_box.currentIndexChanged.connect(self._emit)
        self.language_box.currentIndexChanged.connect(self._emit)
        self.device_box.currentIndexChanged.connect(self._emit)
        self.gpu_box.currentIndexChanged.connect(self._emit)
        self._refresh_memory_hints()

    def retranslate(self) -> None:
        self.back_btn.setText(t("common.back"))
        self.title.setText(t("settings.title"))
        self.hint.setText(t("settings.hint"))
        self.ui_row.set_texts(t("settings.ui_language"), t("settings.ui_language_sub"))
        self.model_row.set_texts(t("settings.model"), t("settings.model_sub"))
        self.speech_row.set_texts(t("settings.speech"), t("settings.speech_sub"))
        self.device_row.set_texts(t("settings.device"), t("settings.device_sub"))
        self.gpu_row.set_texts(t("settings.gpu"), t("settings.gpu_sub"))
        for key, title_key, subtitle_key in _SWITCH_ROWS:
            self.switch_rows[key].set_texts(t(title_key), t(subtitle_key))
        self._refill_boxes()
        self._refresh_memory_hints()

    def _refill_boxes(self) -> None:
        self._fill_combo(
            self.ui_language_box,
            UI_LANGUAGES,
            {key: t(f"settings.ui_{key}") for key in UI_LANGUAGES},
            self.settings.ui_language,
        )
        model_labels = {
            key: f"{t(f'settings.model.{key}')} · {model_memory_text(key)}" for key in MODELS
        }
        self._fill_combo(self.model_box, MODELS, model_labels, self.settings.model)
        self._fill_combo(
            self.language_box,
            LANGUAGES,
            {key: t(f"settings.speech_{key}") for key in LANGUAGES},
            self.settings.language,
        )
        self._fill_combo(
            self.device_box,
            DEVICES,
            {key: t(f"settings.dev.{key}") for key in DEVICES},
            self.settings.device,
        )
        self._fill_gpu_box()

    def _fill_combo(self, box: QComboBox, keys: tuple[str, ...], labels: dict[str, str], current: str) -> None:
        box.blockSignals(True)
        box.clear()
        for key in keys:
            box.addItem(labels[key], key)
        if current in keys:
            box.setCurrentIndex(keys.index(current))
        box.blockSignals(False)

    def _fill_gpu_box(self) -> None:
        current = self.gpu_box.currentData()
        if not isinstance(current, int):
            current = self.settings.gpu_index
        self.gpu_box.blockSignals(True)
        self.gpu_box.clear()
        if self._gpus:
            for gpu in self._gpus:
                self.gpu_box.addItem(gpu.label(), gpu.index)
            self._select_gpu(current)
            self.gpu_box.setEnabled(self.settings.device != "cpu")
        else:
            self.gpu_box.addItem(t("settings.no_gpu"), -1)
            self.gpu_box.setEnabled(False)
        self.gpu_box.blockSignals(False)

    def _select_gpu(self, index: int) -> None:
        for row in range(self.gpu_box.count()):
            if self.gpu_box.itemData(row) == index:
                self.gpu_box.setCurrentIndex(row)
                return
        if self.gpu_box.count():
            self.gpu_box.setCurrentIndex(0)

    def _selected_gpu(self):
        index = self.settings.gpu_index
        for gpu in self._gpus:
            if gpu.index == index:
                return gpu
        return self._gpus[0] if self._gpus else None

    def _refresh_memory_hints(self) -> None:
        device = self.settings.device
        model = self.settings.model or "base"
        vram, ram = model_memory(model)
        gpu = self._selected_gpu()
        self.gpu_box.setEnabled(bool(self._gpus) and device != "cpu")

        if device == "cpu":
            self.model_status.setText(t("settings.cpu_ram", model=model, ram=ram))
            self.gpu_status.setText(t("settings.cpu_now"))
            return

        gpu_line = t("settings.will_use", compute=describe_compute(self.settings))
        if not self._gpus:
            self.model_status.setText(t("settings.no_gpu_hint", model=model, vram=vram, ram=ram))
            self.gpu_status.setText(t("settings.no_gpu_status"))
            return

        available = round((gpu.memory_mb or 0) / 1024) if gpu and gpu.memory_mb else None
        if available is not None and available < vram:
            self.model_status.setText(
                t(
                    "settings.low_vram",
                    model=model,
                    vram=vram,
                    gpu=gpu.name,
                    available=available,
                    ram=ram,
                )
            )
        elif available is not None:
            self.model_status.setText(
                t(
                    "settings.ok_vram",
                    model=model,
                    vram=vram,
                    gpu=gpu.name,
                    available=available,
                    ram=ram,
                )
            )
        else:
            self.model_status.setText(t("settings.generic_mem", model=model, vram=vram, ram=ram))
        self.gpu_status.setText(gpu_line)

    def _emit(self) -> None:
        self.settings.ui_language = self.ui_language_box.currentData() or "auto"
        self.settings.model = self.model_box.currentData()
        self.settings.language = self.language_box.currentData()
        self.settings.device = self.device_box.currentData() or "auto"
        gpu = self.gpu_box.currentData()
        self.settings.gpu_index = int(gpu) if isinstance(gpu, int) and gpu >= 0 else 0
        self.settings.remove_fillers = self.switches["remove_fillers"].isChecked()
        self.settings.split_speakers = self.switches["split_speakers"].isChecked()
        self.settings.denoise = self.switches["denoise"].isChecked()
        self.settings.remove_silence = self.switches["remove_silence"].isChecked()
        self.settings.normalize = self.switches["normalize"].isChecked()
        self.settings.timestamps = self.switches["timestamps"].isChecked()
        set_ui_language(self.settings.ui_language)
        self._refresh_memory_hints()
        self.changed.emit(self.settings)
