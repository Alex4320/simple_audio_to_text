from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from simple_audio_to_text.paths import settings_path
from simple_audio_to_text.services.i18n import UI_LANGUAGES, t

MODELS = (
    "tiny",
    "base",
    "small",
    "medium",
    "large-v2",
    "large-v3",
    "large-v3-turbo",
    "distil-large-v3",
)
MODEL_MEMORY = {
    "tiny": (1, 1),
    "base": (1, 1),
    "small": (2, 2),
    "medium": (5, 5),
    "large-v2": (10, 10),
    "large-v3": (10, 10),
    "large-v3-turbo": (6, 6),
    "distil-large-v3": (4, 4),
}


def model_memory(name: str) -> tuple[int, int]:
    return MODEL_MEMORY.get(name, (2, 2))


def model_memory_text(name: str) -> str:
    vram, ram = model_memory(name)
    return t("settings.mem_label", vram=vram, ram=ram)


LANGUAGES = ("auto", "ru", "en")
DEVICES = ("auto", "cpu", "cuda")


@dataclass
class AppSettings:
    remove_fillers: bool = True
    split_speakers: bool = False
    denoise: bool = True
    remove_silence: bool = True
    normalize: bool = True
    timestamps: bool = False
    language: str = "auto"
    ui_language: str = "auto"
    model: str = "base"
    device: str = "auto"
    gpu_index: int = 0

    def validated(self) -> "AppSettings":
        if self.model not in MODELS:
            self.model = "base"
        if self.language not in LANGUAGES:
            self.language = "auto"
        if self.ui_language not in UI_LANGUAGES:
            self.ui_language = "auto"
        if self.device not in DEVICES:
            self.device = "auto"
        if self.gpu_index < 0:
            self.gpu_index = 0
        return self


def load_settings(path: Path | None = None) -> AppSettings:
    target = path or settings_path()
    if not target.exists():
        return AppSettings()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()
    allowed = {item.name for item in fields(AppSettings)}
    data = {key: raw[key] for key in allowed if key in raw}
    return AppSettings(**data).validated()


def save_settings(settings: AppSettings, path: Path | None = None) -> None:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(settings.validated()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
