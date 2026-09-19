from pathlib import Path

from simple_audio_to_text.paths import app_dir, models_dir


def test_models_live_next_to_the_app() -> None:
    root = app_dir()
    assert (root / "pyproject.toml").is_file()
    folder = models_dir()
    assert folder == root / "models"
    assert folder.is_dir()
    assert folder.name == "models"
