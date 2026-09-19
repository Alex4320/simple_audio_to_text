from __future__ import annotations

from pathlib import Path

import numpy as np

from simple_audio_to_text.services.ffmpeg_bin import ffmpeg_executable
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.process import run_hidden

SAMPLE_RATE = 16_000
RECORD_RATE = 48_000
AUDIO_FILE_SUFFIXES = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
    ".wma",
    ".opus",
    ".aiff",
    ".aif",
    ".webm",
}
VIDEO_FILE_SUFFIXES = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
    ".wmv",
    ".flv",
    ".m4v",
    ".ts",
    ".mts",
    ".m2ts",
    ".3gp",
    ".mpg",
    ".mpeg",
    ".vob",
    ".ogv",
    ".asf",
    ".f4v",
}
AUDIO_SUFFIXES = AUDIO_FILE_SUFFIXES | VIDEO_FILE_SUFFIXES


def is_supported_media(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_SUFFIXES


def is_supported_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_FILE_SUFFIXES


def is_supported_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_FILE_SUFFIXES


def media_filter(suffixes: set[str], label: str) -> str:
    return label + " (" + " ".join(f"*{ext}" for ext in sorted(suffixes)) + ")"


def load_audio(path: Path | str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    command = [
        ffmpeg_executable(),
        "-v",
        "error",
        "-i",
        str(source),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "pipe:1",
    ]
    completed = run_hidden(command, check=False, capture_output=True)
    if completed.returncode != 0 or not completed.stdout:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or t("io.read_fail"))
    audio = np.frombuffer(completed.stdout, dtype=np.float32)
    if audio.size == 0:
        raise RuntimeError(t("io.no_track"))
    return np.ascontiguousarray(audio)


def duration_seconds(path: Path | str) -> float | None:
    command = [ffmpeg_executable(), "-i", str(path)]
    completed = run_hidden(command, check=False, capture_output=True)
    text = completed.stderr.decode("utf-8", errors="replace")
    marker = "Duration: "
    if marker not in text:
        return None
    raw = text.split(marker, 1)[1].split(",", 1)[0].strip()
    if raw.startswith("N/A"):
        return None
    parts = raw.split(":")
    if len(parts) != 3:
        return None
    try:
        hours, minutes, seconds = float(parts[0]), float(parts[1]), float(parts[2])
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


def format_clock(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
