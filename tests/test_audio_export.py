import wave
from pathlib import Path

import numpy as np

from simple_audio_to_text.services.audio_export import extract_audio_file, export_audio, join_takes, write_wav
from simple_audio_to_text.services.audio_io import is_supported_audio, is_supported_video


def test_join_takes_makes_one_recording() -> None:
    first = np.ones(4, dtype=np.float32)
    second = np.full(3, 0.5, dtype=np.float32)
    combined = join_takes([first, second])
    assert combined.tolist() == [1.0, 1.0, 1.0, 1.0, 0.5, 0.5, 0.5]


def test_join_takes_skips_empty() -> None:
    assert join_takes([np.zeros(0, dtype=np.float32)]).size == 0
    out = join_takes([np.zeros(0, dtype=np.float32), np.ones(2, dtype=np.float32)])
    assert out.tolist() == [1.0, 1.0]


def test_write_wav_roundtrip(tmp_path: Path) -> None:
    audio = np.zeros(8000, dtype=np.float32)
    audio[10:20] = 0.25
    path = tmp_path / "clip.wav"
    write_wav(path, audio, 8000)
    with wave.open(str(path), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 8000
        assert wav.getnframes() == 8000


def test_export_wav_and_optional_mp3(tmp_path: Path) -> None:
    audio = np.linspace(-0.2, 0.2, 4800, dtype=np.float32)
    wav_path = tmp_path / "out.wav"
    export_audio(wav_path, audio, 48000)
    assert wav_path.stat().st_size > 100
    mp3_path = tmp_path / "out.mp3"
    try:
        export_audio(mp3_path, audio, 48000)
    except RuntimeError:
        return
    assert mp3_path.stat().st_size > 50


def test_extract_audio_file_keeps_sound(tmp_path: Path) -> None:
    source = tmp_path / "clip.wav"
    dest = tmp_path / "from-video.wav"
    write_wav(source, np.linspace(-0.3, 0.3, 4000, dtype=np.float32), 8000)
    extract_audio_file(source, dest)
    assert dest.stat().st_size > 100
    with wave.open(str(dest), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getnframes() > 0


def test_video_and_audio_suffixes() -> None:
    assert is_supported_video(Path("talk.mp4"))
    assert is_supported_video(Path("clip.mkv"))
    assert not is_supported_video(Path("song.mp3"))
    assert is_supported_audio(Path("song.flac"))
    assert not is_supported_audio(Path("movie.mkv"))
