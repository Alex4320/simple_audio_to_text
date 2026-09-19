from simple_audio_to_text.services.i18n import set_ui_language, t
from simple_audio_to_text.services.postprocess import Segment, format_transcript, remove_fillers
from simple_audio_to_text.services.settings import AppSettings, load_settings, save_settings


def test_remove_fillers_ru_en() -> None:
    text = "Ну вот, это как бы важно, um, you know, реально"
    cleaned = remove_fillers(text)
    assert "ну" not in cleaned.casefold()
    assert "um" not in cleaned.casefold()
    assert "важно" in cleaned
    assert "реально" in cleaned


def test_format_with_speakers_and_timestamps() -> None:
    set_ui_language("en")
    settings = AppSettings(split_speakers=True, timestamps=True, remove_fillers=False)
    text = format_transcript(
        [
            Segment(5, 8, "Привет", speaker=1),
            Segment(9, 12, "Здравствуйте", speaker=2),
        ],
        settings,
    )
    assert t("export.speaker", n=1) in text
    assert t("export.speaker", n=2) in text
    assert "00:05" in text


def test_settings_roundtrip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    original = AppSettings(model="small", language="ru", ui_language="en", split_speakers=True)
    save_settings(original, path)
    loaded = load_settings(path)
    assert loaded.model == "small"
    assert loaded.language == "ru"
    assert loaded.ui_language == "en"
    assert loaded.split_speakers is True
