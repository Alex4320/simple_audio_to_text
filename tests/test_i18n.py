from simple_audio_to_text.services.i18n import (
    _STRINGS,
    audio_export_filter,
    resolve_ui_language,
    set_ui_language,
    t,
    transcript_export_filter,
)
from simple_audio_to_text.services.settings import AppSettings, load_settings, save_settings


def test_catalogs_have_the_same_keys() -> None:
    assert set(_STRINGS["ru"]) == set(_STRINGS["en"])


def test_english_and_russian_strings() -> None:
    set_ui_language("en")
    assert t("common.back") == "Back"
    assert t("settings.ui_language") == "Interface language"
    assert t("export.speaker", n=2) == "Speaker 2"
    set_ui_language("ru")
    assert t("common.back") == "Назад"
    assert t("settings.ui_language") == "Язык интерфейса"
    assert t("export.speaker", n=2) == "Спикер 2"


def test_auto_follows_explicit_preference() -> None:
    assert resolve_ui_language("en") == "en"
    assert resolve_ui_language("ru") == "ru"
    assert resolve_ui_language("auto") in {"ru", "en"}
    assert resolve_ui_language(None) in {"ru", "en"}


def test_ui_language_roundtrip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_settings(AppSettings(ui_language="en", model="small"), path)
    loaded = load_settings(path)
    assert loaded.ui_language == "en"
    assert loaded.model == "small"


def test_invalid_ui_language_falls_back_to_auto() -> None:
    settings = AppSettings(ui_language="de")
    assert settings.validated().ui_language == "auto"


def test_export_filters_follow_language() -> None:
    set_ui_language("en")
    assert "Text (*.txt)" in transcript_export_filter()
    assert "MP3 (*.mp3)" in audio_export_filter()
    set_ui_language("ru")
    assert "Текст (*.txt)" in transcript_export_filter()
    assert "MP3 (*.mp3)" in audio_export_filter()
