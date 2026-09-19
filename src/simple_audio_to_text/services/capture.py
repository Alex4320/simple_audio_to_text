from __future__ import annotations

import sys
import time
from collections.abc import Callable

import numpy as np

from simple_audio_to_text.services.audio_io import SAMPLE_RATE
from simple_audio_to_text.services.devices import AudioSource
from simple_audio_to_text.services.i18n import t

LevelCallback = Callable[[float], None]
ChunkCallback = Callable[[np.ndarray], None]


class CaptureError(RuntimeError):
    pass


def _rms(frame: np.ndarray) -> float:
    if frame.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(frame.astype(np.float32)))))


def _record_sounddevice(
    device_name: str | None,
    stop_flag: Callable[[], bool],
    on_level: LevelCallback,
    on_chunk: ChunkCallback,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    import sounddevice as sd

    device = None
    if device_name:
        for index, item in enumerate(sd.query_devices()):
            if item.get("name") == device_name and int(item.get("max_input_channels") or 0) > 0:
                device = index
                break
    block = 1024

    def callback(indata, frames, _time, status):  # noqa: ARG001
        if status:
            return
        mono = np.mean(indata, axis=1) if indata.ndim > 1 else indata.reshape(-1)
        on_level(_rms(mono))
        on_chunk(mono.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=block,
        device=device,
        callback=callback,
    ):
        while not stop_flag():
            time.sleep(0.03)


def _loopback_microphone(source: AudioSource):
    import soundcard as sc

    if source.device_id:
        for mic in sc.all_microphones(include_loopback=True):
            mic_id = str(getattr(mic, "id", "") or "")
            if getattr(mic, "isloopback", False) and source.device_id in mic_id:
                return mic
        for speaker in sc.all_speakers():
            speaker_id = str(getattr(speaker, "id", "") or "")
            if source.device_id in speaker_id:
                return sc.get_microphone(speaker.name, include_loopback=True)
    if source.device_name:
        try:
            mic = sc.get_microphone(source.device_name, include_loopback=True)
            if mic is not None:
                return mic
        except Exception:
            pass
    speaker = sc.default_speaker()
    try:
        return sc.get_microphone(speaker.name, include_loopback=True)
    except Exception as exc:
        raise CaptureError(t("capture.loopback")) from exc


def _record_loopback(
    source: AudioSource,
    stop_flag: Callable[[], bool],
    on_level: LevelCallback,
    on_chunk: ChunkCallback,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    microphone = _loopback_microphone(source)
    if microphone is None:
        raise CaptureError(t("capture.no_loop"))
    if sys.platform == "win32" and not getattr(microphone, "isloopback", False):
        raise CaptureError(t("capture.no_loopback_dev"))
    with microphone.recorder(samplerate=sample_rate, channels=1) as recorder:
        while not stop_flag():
            frame = recorder.record(numframes=1024).reshape(-1)
            on_level(_rms(frame))
            on_chunk(frame.astype(np.float32, copy=False))


def _linux_monitor_name() -> str | None:
    if sys.platform != "linux":
        return None
    try:
        import pulsectl
    except Exception:
        return None
    try:
        with pulsectl.Pulse("simple-audio-to-text-mon") as pulse:
            server = pulse.server_info()
            default_sink = getattr(server, "default_sink_name", None)
            if default_sink:
                return f"{default_sink}.monitor"
            for source in pulse.source_list():
                name = str(source.name)
                if name.endswith(".monitor"):
                    return name
    except Exception:
        return None
    return None


def record_source(
    source: AudioSource,
    stop_flag: Callable[[], bool],
    on_level: LevelCallback,
    on_chunk: ChunkCallback,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    try:
        if source.kind == "mic":
            _record_sounddevice(source.device_name, stop_flag, on_level, on_chunk, sample_rate)
            return
        if sys.platform == "linux":
            monitor = source.device_name if source.kind == "loopback" else _linux_monitor_name()
            linux_source = AudioSource(
                key=source.key,
                title=source.title,
                kind="loopback",
                device_name=monitor,
            )
            _record_loopback(linux_source, stop_flag, on_level, on_chunk, sample_rate)
            return
        _record_loopback(source, stop_flag, on_level, on_chunk, sample_rate)
    except CaptureError:
        raise
    except Exception as exc:
        raise CaptureError(str(exc) or t("capture.open")) from exc
