from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from simple_audio_to_text.services.audio_io import SAMPLE_RATE
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.settings import AppSettings

FILLERS_RU = (
    "ну",
    "вот",
    "типа",
    "как бы",
    "короче",
    "это самое",
    "в общем",
    "значит",
    "как сказать",
    "блин",
    "ээ",
    "э-э",
    "эм",
    "мм",
    "ммм",
    "аа",
    "ага-ага",
)
FILLERS_EN = (
    "um",
    "uh",
    "erm",
    "ah",
    "like",
    "you know",
    "sort of",
    "kind of",
    "i mean",
    "actually",
    "basically",
    "right",
    "so yeah",
    "yeah",
)


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: int | None = None


def _highpass_chunk(audio: np.ndarray, sample_rate: int, cutoff: float) -> np.ndarray:
    spectrum = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(audio.size, 1.0 / sample_rate)
    spectrum[freqs < cutoff] *= 0.05
    return np.fft.irfft(spectrum, n=audio.size).astype(np.float32, copy=False)


def _highpass(audio: np.ndarray, sample_rate: int, cutoff: float = 80.0) -> np.ndarray:
    if audio.size == 0:
        return audio
    chunk = sample_rate * 30
    if audio.size <= chunk:
        return _highpass_chunk(audio, sample_rate, cutoff)
    parts = [
        _highpass_chunk(audio[start : start + chunk], sample_rate, cutoff)
        for start in range(0, audio.size, chunk)
    ]
    return np.concatenate(parts)


def normalize_audio(audio: np.ndarray, peak: float = 0.95) -> np.ndarray:
    if audio.size == 0:
        return audio
    current = float(np.max(np.abs(audio)))
    if current < 1e-8:
        return audio
    return (audio * (peak / current)).astype(np.float32, copy=False)


def denoise_audio(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    if audio.size < sample_rate // 10:
        return audio
    filtered = _highpass(audio, sample_rate)
    frame = 1024
    hop = 512
    noise_len = min(filtered.size, int(sample_rate * 0.35))
    noise = np.abs(np.fft.rfft(filtered[:noise_len] * np.hanning(noise_len)))
    noise_floor = np.percentile(noise, 70) + 1e-6
    out = np.zeros_like(filtered)
    window = np.hanning(frame)
    for start in range(0, filtered.size - frame, hop):
        chunk = filtered[start : start + frame] * window
        spectrum = np.fft.rfft(chunk)
        magnitude = np.abs(spectrum)
        gate = np.clip(magnitude / (noise_floor * 3.5), 0.0, 1.0)
        restored = np.fft.irfft(spectrum * gate)
        out[start : start + frame] += restored[:frame].astype(np.float32)
    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * 0.95).astype(np.float32)


def remove_silence(
    audio: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    threshold: float = 0.012,
) -> np.ndarray:
    if audio.size == 0:
        return audio
    frame = int(sample_rate * 0.03)
    if frame < 64:
        return audio
    keep: list[np.ndarray] = []
    silent_run = 0
    max_keep_silence = int(0.28 / 0.03)
    for start in range(0, audio.size, frame):
        chunk = audio[start : start + frame]
        if chunk.size < frame // 2:
            keep.append(chunk)
            break
        if float(np.sqrt(np.mean(chunk**2))) >= threshold:
            keep.append(chunk)
            silent_run = 0
            continue
        silent_run += 1
        if silent_run <= max_keep_silence:
            keep.append(chunk)
    if not keep:
        return audio
    return np.concatenate(keep).astype(np.float32, copy=False)


def prepare_audio(audio: np.ndarray, settings: AppSettings) -> np.ndarray:
    prepared = np.ascontiguousarray(audio, dtype=np.float32)
    if settings.normalize:
        prepared = normalize_audio(prepared)
    if settings.denoise:
        prepared = denoise_audio(prepared)
    if settings.remove_silence:
        prepared = remove_silence(prepared)
    if settings.normalize:
        prepared = normalize_audio(prepared)
    return prepared


def _filler_pattern() -> re.Pattern[str]:
    words = sorted(set(FILLERS_RU + FILLERS_EN), key=len, reverse=True)
    escaped = [re.escape(word) for word in words]
    return re.compile(rf"(?<![\w/])(?:{'|'.join(escaped)})(?![\w/])", re.IGNORECASE)


_FILLERS = _filler_pattern()


def remove_fillers(text: str) -> str:
    cleaned = _FILLERS.sub(" ", text)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def format_transcript(segments: list[Segment], settings: AppSettings) -> str:
    lines: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        if settings.remove_fillers:
            text = remove_fillers(text)
        if not text:
            continue
        prefix_parts: list[str] = []
        if settings.split_speakers and segment.speaker is not None:
            prefix_parts.append(t("export.speaker", n=segment.speaker))
        if settings.timestamps:
            from simple_audio_to_text.services.audio_io import format_clock

            prefix_parts.append(format_clock(segment.start))
        if prefix_parts:
            lines.append(f"[{' · '.join(prefix_parts)}]  {text}")
        else:
            lines.append(text)
    if settings.split_speakers:
        return "\n".join(lines)
    return " ".join(lines) if not settings.timestamps else "\n".join(lines)
