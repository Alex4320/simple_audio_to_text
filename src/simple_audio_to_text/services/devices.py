from __future__ import annotations

import ctypes
import os
import re
import sys
from ctypes import wintypes
from dataclasses import dataclass

import sounddevice as sd

from simple_audio_to_text.services.i18n import t

_JUNK_WINDOWS = {
    "zptoolbarparentwnd",
    "default ime",
    "msctfime ui",
    "gdi+ window",
    "tooltips_class32",
    "olemainthreadwndname",
    "ciceroime ui window",
}
_DURATION_TAIL = re.compile(
    r",\s*\d+\s*(?:мин|min|minutes?|сек|sec|seconds?)(?:\s.*)?$",
    re.IGNORECASE,
)
_ZOOM_MEETING = re.compile(
    r"^zoom\s+(конференция|conference|meeting|webinar)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AudioSource:
    key: str
    title: str
    kind: str
    device_name: str | None = None
    device_id: str | None = None
    pid: int | None = None
    detail: str = ""


def _safe_hostapi_name(index: int) -> str:
    try:
        return _display_name(str(sd.query_hostapis(index).get("name", "")))
    except Exception:
        return ""


def _display_name(name: str) -> str:
    if sys.platform != "win32":
        return name
    for encoding in ("cp1251", "cp866"):
        try:
            fixed = name.encode("latin-1").decode(encoding)
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
        if any("а" <= char.lower() <= "я" or char in "ёЁ" for char in fixed):
            return fixed
    return name


def _is_hidden_input_name(name: str) -> bool:
    lower = name.lower()
    if "loopback" in lower or "monitor" in lower:
        return True
    return any(
        token in lower
        for token in (
            "mapper",
            "переназначение",
            "первичный драйвер",
            "primary sound",
        )
    )


def is_mixer_active_session(state: int) -> bool:
    return int(state) == 1


def _sounddevice_inputs() -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    try:
        devices = sd.query_devices()
    except Exception:
        return rows
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels") or 0) <= 0:
            continue
        name = _display_name(str(device.get("name") or f"{t('common.mic')} {index}")).strip()
        if not name or _is_hidden_input_name(name):
            continue
        host = _safe_hostapi_name(int(device.get("hostapi") or 0))
        rows.append((index, name, host))
    return rows


def _sounddevice_input_name(wanted: str) -> str | None:
    wanted_cf = wanted.casefold()
    exact: list[tuple[int, str, str]] = []
    partial: list[tuple[int, str, str]] = []
    for row in _sounddevice_inputs():
        name_cf = row[1].casefold()
        if name_cf == wanted_cf:
            exact.append(row)
        elif wanted_cf in name_cf or name_cf in wanted_cf:
            partial.append(row)
    for group in (exact, partial):
        if not group:
            continue
        wasapi = [item for item in group if "wasapi" in item[2].casefold()]
        chosen = (wasapi or group)[0]
        return chosen[1]
    return None


def _windows_capture_devices() -> list[AudioSource]:
    if sys.platform != "win32":
        return []
    try:
        from pycaw.constants import DEVICE_STATE, EDataFlow
        from pycaw.pycaw import AudioUtilities
    except Exception:
        return []
    default_id = None
    try:
        raw = AudioUtilities.GetMicrophone()
        default_id = raw.GetId() if raw is not None else None
    except Exception:
        default_id = None
    try:
        devices = AudioUtilities.GetAllDevices(
            data_flow=EDataFlow.eCapture.value,
            device_state=DEVICE_STATE.ACTIVE.value,
        )
    except Exception:
        return []
    sources: list[AudioSource] = []
    seen: set[str] = set()
    for device in devices:
        name = str(getattr(device, "FriendlyName", "") or "").strip()
        if not name or _is_hidden_input_name(name):
            continue
        fingerprint = name.casefold()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        device_id = str(getattr(device, "id", "") or "") or None
        is_default = bool(default_id and device_id == default_id)
        sources.append(
            AudioSource(
                key=f"mic:{device_id or name}",
                title=name,
                kind="mic",
                device_name=_sounddevice_input_name(name) or name,
                device_id=device_id,
                detail=t("devices.default") if is_default else t("devices.active"),
            )
        )
    sources.sort(key=lambda item: (item.detail != t("devices.default"), item.title.casefold()))
    return sources


def _sounddevice_microphones() -> list[AudioSource]:
    sources: list[AudioSource] = []
    seen: set[str] = set()
    rows = _sounddevice_inputs()
    wasapi = [item for item in rows if "wasapi" in item[2].casefold()]
    chosen = wasapi or rows
    for index, name, host in chosen:
        fingerprint = name.casefold()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        sources.append(
            AudioSource(
                key=f"mic:{index}",
                title=name,
                kind="mic",
                device_name=name,
                detail=host or t("devices.mic"),
            )
        )
    return sources


def list_microphones() -> list[AudioSource]:
    if sys.platform == "win32":
        windows = _windows_capture_devices()
        if windows:
            return windows
    return _sounddevice_microphones()


def _loopback_from_soundcard() -> list[AudioSource]:
    sources: list[AudioSource] = []
    try:
        import soundcard as sc
    except Exception:
        return sources
    try:
        microphones = sc.all_microphones(include_loopback=True)
    except Exception:
        return sources
    for mic in microphones:
        name = str(getattr(mic, "name", "") or "")
        is_loop = bool(getattr(mic, "isloopback", False)) or "loopback" in name.lower()
        if not is_loop and "monitor" not in name.lower():
            continue
        sources.append(
            AudioSource(
                key=f"loop:{name}",
                title=t("devices.system") if is_loop else name,
                kind="loopback",
                device_name=name,
                device_id=str(getattr(mic, "id", "") or "") or None,
                detail=name,
            )
        )
    return sources


def _resolve_indirect_string(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith("@"):
        return raw
    try:
        buf = ctypes.create_unicode_buffer(512)
        status = ctypes.windll.shlwapi.SHLoadIndirectString(
            os.path.expandvars(raw), buf, len(buf), None
        )
    except Exception:
        return ""
    return buf.value.strip() if status == 0 else ""


def _file_description(path: str | None) -> str:
    if not path or sys.platform != "win32":
        return ""
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return ""
        data = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(path, 0, size, data):
            return ""
        pointer = ctypes.c_void_p()
        length = wintypes.UINT()
        if not ctypes.windll.version.VerQueryValueW(
            data, r"\VarFileInfo\Translation", ctypes.byref(pointer), ctypes.byref(length)
        ):
            return ""
        if not pointer.value:
            return ""
        lang = ctypes.cast(pointer, ctypes.POINTER(wintypes.WORD))
        key = rf"\StringFileInfo\{lang[0]:04x}{lang[1]:04x}\FileDescription"
        if not ctypes.windll.version.VerQueryValueW(
            data, key, ctypes.byref(pointer), ctypes.byref(length)
        ):
            return ""
        return ctypes.wstring_at(pointer.value).strip() if pointer.value else ""
    except Exception:
        return ""


def _window_titles(pid: int) -> list[str]:
    if sys.platform != "win32" or not pid:
        return []
    titles: list[str] = []
    user32 = ctypes.windll.user32
    proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        found = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found))
        if found.value != pid or not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        text = buf.value.strip()
        if text:
            titles.append(text)
        return True

    user32.EnumWindows(proc(callback), 0)
    return titles


def mixer_style_title(
    window_titles: list[str],
    display_name: str = "",
    file_description: str = "",
    process_name: str = "",
) -> str:
    resolved = _resolve_indirect_string(display_name) if display_name.startswith("@") else display_name.strip()
    if resolved and not resolved.startswith("@"):
        return resolved
    usable: list[str] = []
    for raw in window_titles:
        cleaned = _DURATION_TAIL.sub("", raw).strip()
        if not cleaned or cleaned.casefold() in _JUNK_WINDOWS:
            continue
        if _ZOOM_MEETING.match(cleaned):
            return cleaned.split(None, 1)[1]
        usable.append(cleaned)
    if usable:
        return usable[0]
    if file_description:
        return file_description
    return process_name.replace(".exe", "") or t("devices.app")


def _session_endpoint_id(session) -> str | None:
    ident = str(getattr(session, "Identifier", "") or "")
    endpoint = ident.split("|", 1)[0].strip()
    return endpoint or None


def _windows_render_sessions() -> list[tuple[object, str | None, str | None, int]]:
    try:
        from pycaw.api.audiopolicy import IAudioSessionControl2
        from pycaw.constants import DEVICE_STATE, EDataFlow
        from pycaw.pycaw import AudioUtilities
        from pycaw.utils import AudioSession
    except Exception:
        return []
    rows: list[tuple[object, str | None, str | None, int]] = []
    try:
        devices = AudioUtilities.GetAllDevices(
            data_flow=EDataFlow.eRender.value,
            device_state=DEVICE_STATE.ACTIVE.value,
        )
    except Exception:
        devices = []
    if not devices:
        try:
            for session in AudioUtilities.GetAllSessions():
                rows.append((session, None, None, int(getattr(session, "State", 0) or 0)))
        except Exception:
            return []
        return rows
    for device in devices:
        try:
            enumerator = device.AudioSessionManager.GetSessionEnumerator()
            count = enumerator.GetCount()
        except Exception:
            continue
        friendly = str(getattr(device, "FriendlyName", "") or "") or None
        device_id = str(getattr(device, "id", "") or "") or None
        for index in range(count):
            try:
                control = enumerator.GetSession(index)
                if control is None:
                    continue
                session = AudioSession(control.QueryInterface(IAudioSessionControl2))
            except Exception:
                continue
            rows.append((session, device_id, friendly, int(getattr(session, "State", 0) or 0)))
    return rows


def _windows_apps() -> list[AudioSource]:
    if sys.platform != "win32":
        return []
    found: dict[tuple[int, str], tuple[int, AudioSource]] = {}
    for session, device_id, device_name, state in _windows_render_sessions():
        process = getattr(session, "Process", None)
        if process is None:
            continue
        try:
            pid = int(process.pid)
            process_name = str(process.name() or t("devices.app"))
            exe = str(process.exe() or "")
        except Exception:
            continue
        if pid == 0 or not is_mixer_active_session(state):
            continue
        title = mixer_style_title(
            _window_titles(pid),
            display_name=str(getattr(session, "DisplayName", "") or ""),
            file_description=_file_description(exe),
            process_name=process_name,
        )
        endpoint = device_id or _session_endpoint_id(session)
        source = AudioSource(
            key=f"app:{pid}:{title}",
            title=title,
            kind="app",
            device_name=device_name,
            device_id=endpoint,
            pid=pid,
        )
        fingerprint = (pid, title.casefold())
        previous = found.get(fingerprint)
        if previous is None or state >= previous[0]:
            found[fingerprint] = (state, source)
    return sorted((item[1] for item in found.values()), key=lambda item: item.title.casefold())


def _linux_apps() -> list[AudioSource]:
    if sys.platform != "linux":
        return []
    try:
        import pulsectl
    except Exception:
        return []
    found: list[AudioSource] = []
    try:
        with pulsectl.Pulse("simple-audio-to-text") as pulse:
            for sink_input in pulse.sink_input_list():
                props = sink_input.proplist or {}
                title = (
                    props.get("application.name")
                    or props.get("application.process.binary")
                    or t("devices.stream", index=sink_input.index)
                )
                pid_raw = props.get("application.process.id")
                pid = int(pid_raw) if pid_raw and str(pid_raw).isdigit() else None
                found.append(
                    AudioSource(
                        key=f"app:{sink_input.index}",
                        title=str(title),
                        kind="app",
                        pid=pid,
                        device_name=str(sink_input.index),
                        detail=props.get("media.name") or t("devices.playback"),
                    )
                )
    except Exception:
        return []
    return found


def list_applications() -> list[AudioSource]:
    if sys.platform == "win32":
        apps = _windows_apps()
    elif sys.platform == "linux":
        apps = _linux_apps()
    else:
        apps = []
    loopbacks = _loopback_from_soundcard()
    if loopbacks:
        system = loopbacks[0]
        try:
            import soundcard as sc

            default_name = sc.default_speaker().name
            system = next((item for item in loopbacks if item.device_name == default_name), system)
        except Exception:
            pass
        apps = [
            AudioSource(
                key=system.key,
                title=t("devices.system"),
                kind="loopback",
                device_name=system.device_name,
                device_id=system.device_id,
                detail=t("devices.system_detail"),
            ),
            *apps,
        ]
    elif not apps:
        apps = [
            AudioSource(
                key="loop:default",
                title=t("devices.system"),
                kind="loopback",
                detail=t("devices.output"),
            )
        ]
    return apps


def refresh_sources() -> tuple[list[AudioSource], list[AudioSource]]:
    return list_microphones(), list_applications()
