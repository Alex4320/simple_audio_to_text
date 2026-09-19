from simple_audio_to_text.services import hub_progress
from simple_audio_to_text.services.hub_progress import format_bytes, format_download_status, format_speed
from simple_audio_to_text.services.i18n import set_ui_language


def test_format_bytes_and_speed() -> None:
    set_ui_language("ru")
    assert format_bytes(512) == "512 Б"
    assert format_bytes(2048) == "2 КБ"
    assert format_bytes(3.5 * 1024 * 1024) == "3.5 МБ"
    assert format_speed(20 * 1024 * 1024) == "20.0 МБ/с"


def test_format_download_status_includes_percent_and_speed() -> None:
    set_ui_language("ru")
    percent, text = format_download_status(512 * 1024 * 1024, 1024 * 1024 * 1024, 18 * 1024 * 1024)
    assert percent == 50
    assert "50%" in text
    assert "18.0 МБ/с" in text


def test_hub_tqdm_reports_byte_progress() -> None:
    set_ui_language("ru")
    events: list[hub_progress.DownloadProgress] = []
    hub_progress._CALLBACK = events.append
    hub_progress._AGG = hub_progress._Aggregate()
    try:
        bar = hub_progress.HubTqdm(total=1000, unit="B", desc="Reconstructing files")
        bar.update(250)
        bar.close()
    finally:
        hub_progress._CALLBACK = None
        hub_progress._AGG = None
    assert events
    last = events[-1]
    assert last.percent == 25
    assert last.downloaded == 250
    assert "25%" in last.message


def test_hub_tqdm_skips_file_counters() -> None:
    events: list[hub_progress.DownloadProgress] = []
    hub_progress._CALLBACK = events.append
    hub_progress._AGG = hub_progress._Aggregate()
    try:
        bar = hub_progress.HubTqdm(total=5, unit="it", desc="Fetching 5 files")
        bar.update(1)
        bar.close()
    finally:
        hub_progress._CALLBACK = None
        hub_progress._AGG = None
    assert events == []
