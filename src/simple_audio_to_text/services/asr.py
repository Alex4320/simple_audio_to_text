from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

import numpy as np

from simple_audio_to_text.paths import models_dir
from simple_audio_to_text.services.audio_io import SAMPLE_RATE
from simple_audio_to_text.services.diarize import label_speakers
from simple_audio_to_text.services.hub_progress import DownloadProgress, download_whisper_model
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.postprocess import Segment, format_transcript, prepare_audio
from simple_audio_to_text.services.process import run_hidden
from simple_audio_to_text.services.settings import AppSettings

ProgressCallback = Callable[[DownloadProgress], None]

_LOCK = Lock()
_MODEL = None
_MODEL_KEY: tuple[str, str, int] | None = None
_GPU_LOCK = Lock()
_GPU_CACHE = None


@dataclass(frozen=True)
class GpuInfo:
    index: int
    name: str
    memory_mb: int | None = None

    def label(self) -> str:
        if self.memory_mb:
            gigs = max(1, round(self.memory_mb / 1024))
            return f"{self.index}: {self.name} · {gigs} {t('asr.gb')}"
        return f"{self.index}: {self.name}"


@dataclass
class TranscriptResult:
    text: str
    segments: list[Segment]


def cuda_available() -> bool:
    return bool(list_cuda_devices())


def _smi_gpus() -> list[GpuInfo]:
    smi = shutil.which("nvidia-smi")
    if not smi:
        return []
    try:
        completed = run_hidden(
            [
                smi,
                "--query-gpu=index,name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    found: list[GpuInfo] = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            index = int(parts[0])
        except ValueError:
            continue
        memory = None
        if len(parts) >= 3:
            try:
                memory = int(float(parts[2]))
            except ValueError:
                memory = None
        found.append(GpuInfo(index=index, name=parts[1], memory_mb=memory))
    return found


def _ctranslate_gpus() -> list[GpuInfo]:
    try:
        import ctranslate2

        count = int(ctranslate2.get_cuda_device_count())
    except Exception:
        return []
    return [GpuInfo(index=index, name=f"CUDA GPU {index}") for index in range(count)]


def list_cuda_devices(*, refresh: bool = False) -> list[GpuInfo]:
    global _GPU_CACHE
    with _GPU_LOCK:
        if _GPU_CACHE is not None and not refresh:
            return list(_GPU_CACHE)
        found = _smi_gpus() or _ctranslate_gpus()
        _GPU_CACHE = found
        return list(found)


def selected_gpu(settings: AppSettings) -> GpuInfo | None:
    devices = list_cuda_devices()
    if not devices:
        return None
    for item in devices:
        if item.index == settings.gpu_index:
            return item
    return devices[0]


def resolve_device(preference: str) -> str:
    wants_cuda = preference in {"cuda", "auto"}
    has_cuda = bool(list_cuda_devices())
    if preference == "cuda" and not has_cuda:
        raise RuntimeError(t("asr.cuda_missing"))
    if wants_cuda and has_cuda:
        return "cuda"
    return "cpu"


def describe_compute(settings: AppSettings) -> str:
    try:
        device = resolve_device(settings.device)
    except RuntimeError:
        return t("asr.cuda_off", model=settings.model)
    if device == "cpu":
        return t("asr.cpu", model=settings.model)
    gpu = selected_gpu(settings)
    if gpu is None:
        return t("asr.cuda", model=settings.model)
    return t("asr.gpu", name=gpu.name, model=settings.model)


def _compute_type(device: str) -> str:
    return "float16" if device == "cuda" else "int8"


def get_model(
    settings: AppSettings | str,
    device: str | None = None,
    on_progress: ProgressCallback | None = None,
):
    global _MODEL, _MODEL_KEY
    if isinstance(settings, str):
        name = settings
        resolved = resolve_device(device or "auto")
        gpu_index = 0
    else:
        name = settings.model
        resolved = resolve_device(settings.device)
        gpu_index = settings.gpu_index
    key = (name, resolved, gpu_index)
    with _LOCK:
        if _MODEL is not None and _MODEL_KEY == key:
            return _MODEL
        from faster_whisper import WhisperModel

        if on_progress:
            on_progress(DownloadProgress(percent=None, message=t("asr.check_model", name=name)))
        model_path = download_whisper_model(name, on_progress=on_progress)
        if on_progress:
            on_progress(
                DownloadProgress(
                    percent=100,
                    message=t("asr.open_model", name=name),
                )
            )
        kwargs = {
            "device": resolved,
            "compute_type": _compute_type(resolved),
            "download_root": str(models_dir()),
        }
        if resolved == "cuda":
            kwargs["device_index"] = gpu_index
        _MODEL = WhisperModel(model_path, **kwargs)
        _MODEL_KEY = key
        if on_progress:
            on_progress(DownloadProgress(percent=100, message=t("asr.model_ready", name=name)))
        return _MODEL


def transcribe_audio(
    audio: np.ndarray,
    settings: AppSettings,
    on_progress: ProgressCallback | None = None,
) -> TranscriptResult:
    prepared = prepare_audio(np.ascontiguousarray(audio, dtype=np.float32), settings)
    if prepared.size < SAMPLE_RATE // 5:
        raise RuntimeError(t("asr.too_short"))
    model = get_model(settings, on_progress=on_progress)
    if on_progress:
        on_progress(
            DownloadProgress(
                percent=None,
                message=t("asr.recognize_on", runtime=describe_compute(settings)),
            )
        )
    language = None if settings.language == "auto" else settings.language
    bits, _info = model.transcribe(
        prepared,
        language=language,
        vad_filter=True,
        beam_size=5,
        word_timestamps=settings.split_speakers or settings.timestamps,
        condition_on_previous_text=True,
    )
    segments = [
        Segment(start=item.start, end=item.end, text=item.text.strip())
        for item in bits
        if item.text and item.text.strip()
    ]
    if settings.split_speakers:
        segments = label_speakers(prepared, segments)
    return TranscriptResult(text=format_transcript(segments, settings), segments=segments)


def transcribe_chunk(
    audio: np.ndarray,
    settings: AppSettings,
    prompt: str = "",
) -> list[Segment]:
    prepared = np.ascontiguousarray(audio, dtype=np.float32)
    if prepared.size < SAMPLE_RATE // 4:
        return []
    model = get_model(settings)
    language = None if settings.language == "auto" else settings.language
    bits, _info = model.transcribe(
        prepared,
        language=language,
        vad_filter=True,
        beam_size=3,
        condition_on_previous_text=True,
        initial_prompt=prompt[-240:] if prompt else None,
    )
    return [
        Segment(start=item.start, end=item.end, text=item.text.strip())
        for item in bits
        if item.text and item.text.strip()
    ]
