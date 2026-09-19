import subprocess
import sys

from simple_audio_to_text.services import asr
from simple_audio_to_text.services.asr import GpuInfo
from simple_audio_to_text.services.process import hidden_kwargs, silence_child_consoles


def test_hidden_kwargs_hide_windows_console() -> None:
    kwargs = hidden_kwargs()
    if sys.platform != "win32":
        assert kwargs == {}
        return
    assert kwargs["creationflags"] & getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    assert kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW


def test_list_cuda_devices_uses_cache(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_smi() -> list[GpuInfo]:
        calls["n"] += 1
        return [GpuInfo(0, "Test GPU", 8192)]

    monkeypatch.setattr(asr, "_smi_gpus", fake_smi)
    monkeypatch.setattr(asr, "_ctranslate_gpus", lambda: [])
    asr._GPU_CACHE = None
    first = asr.list_cuda_devices()
    second = asr.list_cuda_devices()
    assert calls["n"] == 1
    assert first == second
    asr.list_cuda_devices(refresh=True)
    assert calls["n"] == 2
    asr._GPU_CACHE = None


def test_silence_child_consoles_is_idempotent() -> None:
    silence_child_consoles()
    silence_child_consoles()
    if sys.platform == "win32":
        assert subprocess.Popen is not None
