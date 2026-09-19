from pathlib import Path

from simple_audio_to_text.services.export import export_transcript
from simple_audio_to_text.services.i18n import set_ui_language, t
from simple_audio_to_text.services.postprocess import Segment
from simple_audio_to_text.services.settings import AppSettings


def test_export_popular_formats(tmp_path: Path) -> None:
    set_ui_language("ru")
    settings = AppSettings(remove_fillers=False, split_speakers=True, timestamps=True)
    segments = [
        Segment(1.0, 3.2, "Привет", speaker=1),
        Segment(3.5, 6.0, "Здравствуйте", speaker=2),
    ]
    text = "Привет Здравствуйте"
    cases = {
        ".txt": "Привет",
        ".srt": "00:00:01,000 --> 00:00:03,200",
        ".vtt": "WEBVTT",
        ".json": '"speaker": 1',
        ".md": f"# {t('export.heading')}",
    }
    for suffix, marker in cases.items():
        path = tmp_path / f"out{suffix}"
        export_transcript(path, text, segments, settings)
        body = path.read_text(encoding="utf-8")
        assert marker in body

    docx = tmp_path / "out.docx"
    export_transcript(docx, text, segments, settings)
    assert docx.stat().st_size > 200


def test_settings_keep_cuda_choice(tmp_path: Path) -> None:
    from simple_audio_to_text.services.settings import load_settings, save_settings

    path = tmp_path / "settings.json"
    save_settings(AppSettings(device="cuda", model="large-v3", gpu_index=1, ui_language="en"), path)
    loaded = load_settings(path)
    assert loaded.device == "cuda"
    assert loaded.model == "large-v3"
    assert loaded.gpu_index == 1
    assert loaded.ui_language == "en"


def test_model_memory_labels() -> None:
    from simple_audio_to_text.services.settings import model_memory, model_memory_text

    set_ui_language("ru")
    assert model_memory("large-v3") == (10, 10)
    assert model_memory("tiny") == (1, 1)
    assert "VRAM" in model_memory_text("medium")
    assert "ОЗУ" in model_memory_text("medium")
    set_ui_language("en")
    assert "RAM" in model_memory_text("medium")


def test_describe_compute_cpu() -> None:
    from simple_audio_to_text.services.asr import describe_compute

    text = describe_compute(AppSettings(device="cpu", model="large-v3"))
    assert "CPU" in text
    assert "large-v3" in text
