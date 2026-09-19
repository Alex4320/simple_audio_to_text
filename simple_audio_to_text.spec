# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

datas = []
_SPEC_DIR = Path(SPECPATH) if "SPECPATH" in globals() else Path.cwd()
_ASSET_DIR = (_SPEC_DIR / "src" / "simple_audio_to_text" / "assets").resolve()
if _ASSET_DIR.is_dir():
    for _file in _ASSET_DIR.iterdir():
        if _file.suffix.lower() in {".png", ".ico"}:
            datas.append((str(_file), "assets"))
            datas.append((str(_file), "simple_audio_to_text/assets"))
_ICON = str(_ASSET_DIR / "app.ico") if (_ASSET_DIR / "app.ico").is_file() else None
binaries = []
hiddenimports = [
    "simple_audio_to_text",
    "simple_audio_to_text.app",
    "sounddevice",
    "soundcard",
    "numpy",
    "faster_whisper",
    "ctranslate2",
    "av",
    "imageio_ffmpeg",
    "platformdirs",
    "psutil",
]


def _is_qml_path(path) -> bool:
    text = str(path).replace("\\", "/").lower()
    return "/qml/" in text or "qt6qml" in text or "qmlassetdownloader" in text


for package in (
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "tokenizers",
    "imageio_ffmpeg",
    "sounddevice",
    "av",
):
    try:
        collected_datas, collected_binaries, collected_hidden = collect_all(package)
    except Exception:
        continue
    datas += collected_datas
    binaries += collected_binaries
    hiddenimports += collected_hidden

datas = [item for item in datas if not _is_qml_path(item[0])]
binaries = [item for item in binaries if not _is_qml_path(item[0])]

a = Analysis(
    ["src/simple_audio_to_text/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtQuickControls2",
        "PySide6.QtQuickWidgets",
        "PySide6.QtMultimedia",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtPdf",
        "PySide6.Qt3DCore",
        "tkinter",
    ],
    noarchive=False,
)
a.datas = [item for item in a.datas if not _is_qml_path(item[0])]
a.binaries = [item for item in a.binaries if not _is_qml_path(item[0])]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SpeechToText",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=_ICON,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SpeechToText",
)
