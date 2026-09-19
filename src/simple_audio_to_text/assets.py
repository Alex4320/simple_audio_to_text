from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget

_ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def assets_dir() -> Path:
    here = Path(__file__).resolve().parent / "assets"
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates = (
            meipass / "assets",
            Path(sys.executable).parent / "assets",
            here,
        )
    else:
        candidates = (here,)
    for path in candidates:
        if (path / "logo.png").is_file() or (path / "app.ico").is_file():
            return path
    return here


def logo_path() -> Path:
    png = assets_dir() / "logo.png"
    return png if png.is_file() else assets_dir() / "app.ico"


def logo_pixmap(logical: int, widget: QWidget | None = None) -> QPixmap:
    source = QPixmap(str(logo_path()))
    if source.isNull():
        return source
    ratio = widget.devicePixelRatio() if widget is not None else 1.0
    ratio = ratio or 1.0
    pixels = max(1, int(round(logical * ratio)))
    scaled = source.scaled(
        pixels,
        pixels,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(ratio)
    return scaled


def app_icon() -> QIcon:
    folder = assets_dir()
    icon = QIcon()
    for size in _ICON_SIZES:
        path = folder / f"logo-{size}.png"
        if path.is_file():
            icon.addFile(str(path), QSize(size, size))
    png = folder / "logo.png"
    if png.is_file():
        icon.addFile(str(png))
    ico = folder / "app.ico"
    if ico.is_file() and icon.isNull():
        icon.addFile(str(ico))
    return icon
