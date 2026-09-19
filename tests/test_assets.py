from simple_audio_to_text.assets import assets_dir, logo_path


def test_logo_files_exist() -> None:
    folder = assets_dir()
    assert (folder / "logo.png").is_file()
    assert (folder / "logo-32.png").is_file()
    assert (folder / "app.ico").is_file()
    assert logo_path().is_file()
    assert logo_path().stat().st_size > 1000
