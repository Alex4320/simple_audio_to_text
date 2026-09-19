import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from simple_audio_to_text.services.i18n import set_ui_language, t
from simple_audio_to_text.services.settings import AppSettings
from simple_audio_to_text.ui.main_window import MainWindow


def _app() -> QApplication:
    existing = QApplication.instance()
    return existing if existing is not None else QApplication([])


def test_main_window_switches_language() -> None:
    _app()
    window = MainWindow(AppSettings(ui_language="ru", device="cpu"))
    assert not window.windowIcon().isNull()
    assert window.home.title.text() == t("home.title")
    assert window.settings_page.title.text() == "Настройки"
    window.settings.ui_language = "en"
    set_ui_language("en")
    window._ui_language = "ru"
    window._settings_changed(window.settings)
    assert window.home.title.text() == "Speech to text"
    assert window.settings_page.title.text() == "Settings"
    assert window.settings_page.back_btn.text() == "Back"
    assert window.file_page.run_btn.text() == "Transcribe"
    assert window.live_page.start_btn.text() == "Start"
    assert window.record_page.export_btn.text() == "Export"
    assert window.video_page.run_btn.text() == "Convert"
