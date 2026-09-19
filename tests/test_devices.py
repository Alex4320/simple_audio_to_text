from simple_audio_to_text.services.devices import is_mixer_active_session, mixer_style_title


def test_zoom_workplace_uses_window_title() -> None:
    title = mixer_style_title(
        ["Zoom Workplace"],
        file_description="Zoom Meetings",
        process_name="Zoom.exe",
    )
    assert title == "Zoom Workplace"


def test_zoom_conference_matches_mixer() -> None:
    title = mixer_style_title(
        ["ZPToolBarParentWnd", "Zoom Конференция, 40 мин "],
        file_description="Zoom Meetings",
        process_name="Zoom.exe",
    )
    assert title == "Конференция"


def test_prefers_session_display_name() -> None:
    title = mixer_style_title(
        ["Something"],
        display_name="Chrome",
        process_name="chrome.exe",
    )
    assert title == "Chrome"


def test_mixer_keeps_only_active_sessions() -> None:
    assert is_mixer_active_session(1)
    assert not is_mixer_active_session(0)
    assert not is_mixer_active_session(2)
