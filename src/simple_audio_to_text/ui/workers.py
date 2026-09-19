from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal

from simple_audio_to_text.services.asr import TranscriptResult, describe_compute, get_model, transcribe_audio, transcribe_chunk
from simple_audio_to_text.services.audio_export import extract_audio_file
from simple_audio_to_text.services.audio_io import RECORD_RATE, SAMPLE_RATE, load_audio
from simple_audio_to_text.services.capture import CaptureError, record_source
from simple_audio_to_text.services.devices import AudioSource
from simple_audio_to_text.services.diarize import label_speakers
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.postprocess import Segment, format_transcript
from simple_audio_to_text.services.settings import AppSettings


@dataclass
class VideoConvertResult:
    audio_path: Path
    transcript: TranscriptResult | None = None


class FileWorker(QThread):
    status = Signal(str)
    progress = Signal(object)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, path: Path, settings: AppSettings) -> None:
        super().__init__()
        self.path = path
        self.settings = settings

    def run(self) -> None:
        try:
            self.status.emit(t("worker.read_file"))
            audio = load_audio(self.path)
            result = transcribe_audio(audio, self.settings, on_progress=self.progress.emit)
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc) or t("worker.file_fail"))


class VideoWorker(QThread):
    status = Signal(str)
    progress = Signal(object)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, source: Path, dest: Path, settings: AppSettings, transcribe: bool) -> None:
        super().__init__()
        self.source = source
        self.dest = dest
        self.settings = settings
        self.transcribe = transcribe

    def run(self) -> None:
        try:
            self.status.emit(t("worker.extract"))
            extract_audio_file(self.source, self.dest)
            if not self.transcribe:
                self.finished_ok.emit(VideoConvertResult(self.dest))
                return
            self.status.emit(t("worker.read_extracted"))
            audio = load_audio(self.dest)
            result = transcribe_audio(audio, self.settings, on_progress=self.progress.emit)
            self.finished_ok.emit(VideoConvertResult(self.dest, result))
        except Exception as exc:
            self.failed.emit(str(exc) or t("worker.video_fail"))


class LiveWorker(QThread):
    level = Signal(float)
    text_changed = Signal(str)
    segments_changed = Signal(object)
    status = Signal(str)
    progress = Signal(object)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, source: AudioSource, settings: AppSettings) -> None:
        super().__init__()
        self.source = source
        self.settings = settings
        self._stop = False
        self._pause = False

    def request_stop(self) -> None:
        self._stop = True

    def set_paused(self, paused: bool) -> None:
        self._pause = paused

    def run(self) -> None:
        chunk_target = int(SAMPLE_RATE * 3.4)
        overlap = int(SAMPLE_RATE * 0.45)
        frames: queue.Queue[np.ndarray | None] = queue.Queue()
        recorded: list[np.ndarray] = []
        segments: list[Segment] = []
        pending = np.zeros(0, dtype=np.float32)
        prompt = ""
        cursor = 0.0
        error: str | None = None
        heard = False
        warned_quiet = False
        started_at = time.time()

        def on_level(value: float) -> None:
            nonlocal heard
            if value > 0.012:
                heard = True
            self.level.emit(min(1.0, value * 8.0))

        def on_chunk(frame: np.ndarray) -> None:
            if self._pause:
                return
            frames.put(frame.copy())

        def capture() -> None:
            nonlocal error
            try:
                record_source(self.source, lambda: self._stop, on_level, on_chunk)
            except CaptureError as exc:
                error = str(exc)
            except Exception as exc:
                error = str(exc) or t("worker.record_fail")
            finally:
                frames.put(None)

        runtime = describe_compute(self.settings)
        self.status.emit(t("worker.load_model", runtime=runtime))
        try:
            get_model(self.settings, on_progress=self.progress.emit)
        except Exception as exc:
            self.failed.emit(str(exc) or t("worker.model_fail"))
            return
        self.progress.emit(None)

        threading.Thread(target=capture, daemon=True).start()
        self.status.emit(t("worker.listen", title=self.source.title, runtime=runtime))

        while True:
            try:
                frame = frames.get(timeout=0.15)
            except queue.Empty:
                if not heard and not self._stop and time.time() - started_at > 5:
                    warned_quiet = True
                    self.status.emit(t("worker.quiet"))
                if self._stop:
                    continue
                continue
            if frame is None:
                break
            if heard and warned_quiet:
                warned_quiet = False
                self.status.emit(t("worker.listen_short", title=self.source.title))
            recorded.append(frame)
            pending = np.concatenate([pending, frame])
            if pending.size < chunk_target:
                continue
            piece = pending
            self.status.emit(t("worker.recognize"))
            try:
                bits = transcribe_chunk(piece, self.settings, prompt)
            except Exception as exc:
                self.failed.emit(str(exc))
                self._stop = True
                continue
            for item in bits:
                segments.append(Segment(cursor + item.start, cursor + item.end, item.text))
            if bits:
                prompt = " ".join(item.text for item in bits)
                self.text_changed.emit(format_transcript(segments, self.settings))
                self.segments_changed.emit(list(segments))
            cursor += max(0.0, (piece.size - overlap) / SAMPLE_RATE)
            pending = pending[-overlap:] if pending.size > overlap else np.zeros(0, dtype=np.float32)

        if error:
            self.failed.emit(error)
            return
        try:
            if pending.size > SAMPLE_RATE // 3:
                bits = transcribe_chunk(pending, self.settings, prompt)
                for item in bits:
                    segments.append(Segment(cursor + item.start, cursor + item.end, item.text))
            audio = np.concatenate(recorded) if recorded else np.zeros(0, dtype=np.float32)
            if self.settings.split_speakers and audio.size and segments:
                self.status.emit(t("worker.speakers"))
                segments = label_speakers(audio, segments)
            text = format_transcript(segments, self.settings)
            result = TranscriptResult(text=text, segments=segments)
            self.text_changed.emit(text)
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc) or t("worker.live_fail"))


class RecordWorker(QThread):
    level = Signal(float)
    elapsed = Signal(float)
    status = Signal(str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, source: AudioSource, sample_rate: int = RECORD_RATE) -> None:
        super().__init__()
        self.source = source
        self.sample_rate = sample_rate
        self._stop = False
        self._pause = False

    def request_stop(self) -> None:
        self._stop = True

    def set_paused(self, paused: bool) -> None:
        self._pause = paused

    def run(self) -> None:
        chunks: list[np.ndarray] = []
        samples = 0
        last_emit = 0.0
        error: str | None = None
        heard = False
        started_at = time.time()

        def on_level(value: float) -> None:
            nonlocal heard
            if value > 0.012:
                heard = True
            self.level.emit(min(1.0, value * 8.0))

        def on_chunk(frame: np.ndarray) -> None:
            nonlocal samples, last_emit
            if self._pause:
                return
            piece = np.ascontiguousarray(frame, dtype=np.float32).reshape(-1)
            chunks.append(piece)
            samples += piece.size
            now = time.monotonic()
            if now - last_emit >= 0.2:
                last_emit = now
                self.elapsed.emit(samples / self.sample_rate)

        try:
            self.status.emit(t("worker.record", title=self.source.title))
            record_source(self.source, lambda: self._stop, on_level, on_chunk, self.sample_rate)
        except CaptureError as exc:
            error = str(exc)
        except Exception as exc:
            error = str(exc) or t("worker.record_fail")
        if error:
            self.failed.emit(error)
            return
        audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
        if not heard and audio.size == 0 and time.time() - started_at > 2:
            self.status.emit(t("worker.empty_take"))
        self.elapsed.emit(audio.size / self.sample_rate)
        self.finished_ok.emit(audio)
