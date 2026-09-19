from __future__ import annotations

import tempfile
import wave
from pathlib import Path

import numpy as np

from simple_audio_to_text.services.ffmpeg_bin import ffmpeg_executable
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.process import run_hidden

AUDIO_EXPORT_FILTER = (
    "WAV (*.wav);;"
    "MP3 (*.mp3);;"
    "FLAC (*.flac);;"
    "OGG Vorbis (*.ogg);;"
    "M4A AAC (*.m4a);;"
    "Opus (*.opus)"
)

_FFMPEG_CODECS = {
    ".mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
    ".flac": ["-c:a", "flac"],
    ".ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    ".m4a": ["-c:a", "aac", "-b:a", "192k"],
    ".aac": ["-c:a", "aac", "-b:a", "192k"],
    ".opus": ["-c:a", "libopus", "-b:a", "96k"],
    ".wav": ["-c:a", "pcm_s16le"],
}


def join_takes(takes: list[np.ndarray]) -> np.ndarray:
    ready = [np.ascontiguousarray(item, dtype=np.float32).reshape(-1) for item in takes if item.size]
    if not ready:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(ready)


def write_wav(path: Path | str, audio: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(np.ascontiguousarray(audio, dtype=np.float32).reshape(-1), -1.0, 1.0)
    samples = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(sample_rate))
        wav.writeframes(samples.tobytes())


def export_audio(path: Path | str, audio: np.ndarray, sample_rate: int) -> None:
    target = Path(path)
    if audio.size == 0:
        raise RuntimeError(t("export.no_audio"))
    suffix = target.suffix.lower()
    if not suffix:
        target = target.with_suffix(".wav")
        suffix = ".wav"
    if suffix == ".wav":
        write_wav(target, audio, sample_rate)
        return
    extra = _FFMPEG_CODECS.get(suffix)
    if extra is None:
        raise RuntimeError(t("export.unknown", suffix=suffix))
    with tempfile.TemporaryDirectory(prefix="sat-audio-") as folder:
        source = Path(folder) / "take.wav"
        write_wav(source, audio, sample_rate)
        command = [
            ffmpeg_executable(),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            *extra,
            str(target),
        ]
        completed = run_hidden(command, check=False, capture_output=True)
    if completed.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or t("export.save_fail", suffix=suffix))


def extract_audio_file(source: Path | str, dest: Path | str) -> None:
    src = Path(source)
    target = Path(dest)
    if not src.exists():
        raise FileNotFoundError(src)
    suffix = target.suffix.lower() or ".wav"
    if not target.suffix:
        target = target.with_suffix(suffix)
    extra = _FFMPEG_CODECS.get(suffix)
    if extra is None:
        raise RuntimeError(t("export.unknown", suffix=suffix))
    command = [
        ffmpeg_executable(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vn",
        "-sn",
        "-dn",
        *extra,
        str(target),
    ]
    completed = run_hidden(command, check=False, capture_output=True)
    if completed.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or t("export.extract_fail"))
