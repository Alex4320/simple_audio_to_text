from __future__ import annotations

import subprocess
import sys
from typing import Any

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
_POPEN_PATCHED = False
_ORIGINAL_POPEN = subprocess.Popen


def hidden_kwargs() -> dict[str, Any]:
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "startupinfo": startupinfo,
        "creationflags": _CREATE_NO_WINDOW,
    }


def _merge_hidden(kwargs: dict[str, Any]) -> dict[str, Any]:
    extra = hidden_kwargs()
    if not extra:
        return kwargs
    merged = dict(kwargs)
    merged["creationflags"] = merged.get("creationflags", 0) | extra["creationflags"]
    merged.setdefault("startupinfo", extra["startupinfo"])
    return merged


def run_hidden(command, **kwargs) -> subprocess.CompletedProcess:
    kwargs = _merge_hidden(kwargs)
    if "input" not in kwargs:
        kwargs.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.run(command, **kwargs)


def silence_child_consoles() -> None:
    """Stop Windows from flashing a console for ffmpeg, nvidia-smi, and similar tools."""
    global _POPEN_PATCHED
    if sys.platform != "win32" or _POPEN_PATCHED:
        return

    def hidden_popen(*args, **kwargs):
        return _ORIGINAL_POPEN(*args, **_merge_hidden(kwargs))

    subprocess.Popen = hidden_popen  # type: ignore[misc]
    _POPEN_PATCHED = True
