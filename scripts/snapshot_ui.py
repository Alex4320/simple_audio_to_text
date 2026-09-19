from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from simple_audio_to_text.services.settings import AppSettings
from simple_audio_to_text.ui.main_window import MainWindow
from simple_audio_to_text.ui.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow(AppSettings())
    window.resize(1080, 740)
    window.show()
    app.processEvents()
    out = Path("dist-preview")
    out.mkdir(exist_ok=True)
    pages = {
        "home": window.home,
        "file": window.file_page,
        "live": window.live_page,
        "settings": window.settings_page,
    }
    for name, page in pages.items():
        window.stack.setCurrentWidget(page)
        app.processEvents()
        window.grab().save(str(out / f"{name}.png"))
    print(out.resolve())


if __name__ == "__main__":
    main()
