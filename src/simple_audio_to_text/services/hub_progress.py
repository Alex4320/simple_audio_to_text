from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass

from tqdm.auto import tqdm

from simple_audio_to_text.paths import models_dir
from simple_audio_to_text.services.i18n import t

_CALLBACK: Callable[[DownloadProgress], None] | None = None
_AGG: _Aggregate | None = None


@dataclass(frozen=True)
class DownloadProgress:
    percent: int | None
    message: str
    downloaded: int = 0
    total: int = 0
    speed_bps: float = 0.0


@dataclass
class _Aggregate:
    downloaded: int = 0
    total: int = 0
    speed_bps: float = 0.0
    has_reconstruct: bool = False


def format_bytes(value: float) -> str:
    if value >= 1024**3:
        return f"{value / 1024**3:.1f} {t('progress.gb')}"
    if value >= 1024**2:
        return f"{value / 1024**2:.1f} {t('progress.mb')}"
    if value >= 1024:
        return f"{value / 1024:.0f} {t('progress.kb')}"
    return f"{int(value)} {t('progress.b')}"


def format_speed(bytes_per_sec: float) -> str:
    return t("progress.speed", size=format_bytes(bytes_per_sec))


def format_download_status(current: int, total: int, rate: float) -> tuple[int | None, str]:
    if total > 0:
        percent = max(0, min(100, int(current * 100 / total)))
        text = t(
            "progress.load",
            current=format_bytes(current),
            total=format_bytes(total),
            percent=percent,
        )
        if rate > 0:
            text += f" · {format_speed(rate)}"
        return percent, text
    text = t("progress.load_partial", current=format_bytes(current))
    if rate > 0:
        text += f" · {format_speed(rate)}"
    return None, text


class HubTqdm(tqdm):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.pop("name", None)
        kwargs["disable"] = False
        kwargs.setdefault("mininterval", 0.2)
        kwargs.setdefault("miniters", 1)
        kwargs.setdefault("file", io.StringIO())
        super().__init__(*args, **kwargs)
        self._notify()

    def update(self, n: float | None = 1) -> bool | None:
        changed = super().update(n)
        self._notify()
        return changed

    def refresh(self, *args, **kwargs):
        result = super().refresh(*args, **kwargs)
        self._notify()
        return result

    def set_description(self, desc: str | None = None, refresh: bool = True):
        result = super().set_description(desc, refresh=refresh)
        self._notify()
        return result

    def set_description_str(self, desc: str | None = None, refresh: bool = True):
        result = super().set_description_str(desc, refresh=refresh)
        self._notify()
        return result

    def close(self) -> None:
        self._notify()
        super().close()

    def _notify(self) -> None:
        if _CALLBACK is None:
            return
        if str(getattr(self, "unit", "") or "") != "B":
            return
        desc = str(self.desc or "")
        current = int(self.n or 0)
        total = int(self.total or 0)
        rate = float(self.format_dict.get("rate") or 0.0)
        if _AGG is not None:
            if "Download" in desc:
                if rate > 0:
                    _AGG.speed_bps = rate
                if not _AGG.has_reconstruct:
                    _AGG.downloaded = current
                    if total:
                        _AGG.total = total
            else:
                _AGG.has_reconstruct = True
                _AGG.downloaded = current
                if total:
                    _AGG.total = total
                if rate > 0:
                    _AGG.speed_bps = rate
            current, total, rate = _AGG.downloaded, _AGG.total, _AGG.speed_bps
        percent, message = format_download_status(current, total, rate)
        _CALLBACK(
            DownloadProgress(
                percent=percent,
                message=message,
                downloaded=current,
                total=total,
                speed_bps=rate,
            )
        )


def download_whisper_model(
    name: str,
    on_progress: Callable[[DownloadProgress], None] | None = None,
) -> str:
    from faster_whisper.utils import _MODELS

    global _CALLBACK, _AGG
    repo_id = name if "/" in name else _MODELS.get(name)
    if repo_id is None:
        raise ValueError(t("asr.unknown_model", name=name))
    previous = _CALLBACK
    previous_agg = _AGG
    _CALLBACK = on_progress
    _AGG = _Aggregate()
    try:
        import huggingface_hub

        return huggingface_hub.snapshot_download(
            repo_id,
            cache_dir=str(models_dir()),
            allow_patterns=[
                "config.json",
                "preprocessor_config.json",
                "model.bin",
                "tokenizer.json",
                "vocabulary.*",
            ],
            tqdm_class=HubTqdm,
        )
    finally:
        _CALLBACK = previous
        _AGG = previous_agg
