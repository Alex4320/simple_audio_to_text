from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from simple_audio_to_text.assets import app_icon
from simple_audio_to_text.services.i18n import set_ui_language, t
from simple_audio_to_text.services.process import silence_child_consoles
from simple_audio_to_text.services.settings import load_settings
from simple_audio_to_text.ui.main_window import MainWindow
from simple_audio_to_text.ui.theme import apply_theme


def main() -> int:
    silence_child_consoles()
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    settings = load_settings()
    set_ui_language(settings.ui_language)
    app = QApplication(sys.argv)
    app.setApplicationName(t("app.title"))
    app.setOrganizationName("SimpleAudioToText")
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    apply_theme(app)
    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
