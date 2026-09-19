from __future__ import annotations

import numpy as np

from simple_audio_to_text.services.audio_io import SAMPLE_RATE
from simple_audio_to_text.services.postprocess import Segment


def _frames(audio: np.ndarray, sample_rate: int, ms: float = 30.0) -> np.ndarray:
    frame = max(64, int(sample_rate * ms / 1000.0))
    count = audio.size // frame
    if count == 0:
        return np.empty((0, frame), dtype=np.float32)
    return audio[: count * frame].reshape(count, frame)


def _log_bands(frames: np.ndarray, sample_rate: int, bands: int = 16) -> np.ndarray:
    windowed = frames * np.hanning(frames.shape[1])
    spectrum = np.abs(np.fft.rfft(windowed, axis=1)) + 1e-8
    freqs = np.fft.rfftfreq(frames.shape[1], 1.0 / sample_rate)
    edges = np.geomspace(80, max(1200, sample_rate / 2 - 1), bands + 1)
    features = np.zeros((frames.shape[0], bands), dtype=np.float32)
    for index, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (freqs >= low) & (freqs < high)
        if not np.any(mask):
            continue
        features[:, index] = np.log(spectrum[:, mask].mean(axis=1))
    return features


def _kmeans(features: np.ndarray, k: int, rounds: int = 12) -> np.ndarray:
    rng = np.random.default_rng(7)
    centers = features[rng.choice(features.shape[0], size=k, replace=False)]
    labels = np.zeros(features.shape[0], dtype=np.int32)
    for _ in range(rounds):
        distances = ((features[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1).astype(np.int32)
        for cluster in range(k):
            members = features[labels == cluster]
            if len(members):
                centers[cluster] = members.mean(axis=0)
    return labels


def _choose_k(features: np.ndarray, max_k: int = 3) -> int:
    if features.shape[0] < 8:
        return 1
    best_k = 1
    best_score = float("inf")
    limit = min(max_k, features.shape[0] // 4)
    for k in range(1, max(2, limit + 1)):
        labels = _kmeans(features, k)
        if len(set(labels.tolist())) < k:
            continue
        inertia = 0.0
        for cluster in range(k):
            members = features[labels == cluster]
            if not len(members):
                continue
            inertia += float(((members - members.mean(axis=0)) ** 2).sum())
        penalty = inertia + 0.18 * k * features.shape[0]
        if penalty < best_score:
            best_score = penalty
            best_k = k
    return best_k


def label_speakers(audio: np.ndarray, segments: list[Segment], sample_rate: int = SAMPLE_RATE) -> list[Segment]:
    if not segments:
        return segments
    frames = _frames(audio, sample_rate)
    if frames.shape[0] < 6:
        return [Segment(item.start, item.end, item.text, 1) for item in segments]
    energy = np.sqrt((frames**2).mean(axis=1))
    voiced = energy > max(0.008, float(np.percentile(energy, 35)))
    if voiced.sum() < 6:
        return [Segment(item.start, item.end, item.text, 1) for item in segments]
    features = _log_bands(frames[voiced], sample_rate)
    features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-6)
    k = _choose_k(features)
    labels = _kmeans(features, k) + 1
    frame_ms = 0.03
    voiced_index = np.flatnonzero(voiced)
    labeled = []
    for segment in segments:
        start_f = int(segment.start / frame_ms)
        end_f = max(start_f + 1, int(segment.end / frame_ms))
        votes: list[int] = []
        for frame_i, label in zip(voiced_index, labels):
            if start_f <= int(frame_i) < end_f:
                votes.append(int(label))
        speaker = max(set(votes), key=votes.count) if votes else 1
        labeled.append(Segment(segment.start, segment.end, segment.text, speaker))
    return labeled
