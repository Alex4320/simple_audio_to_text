from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from simple_audio_to_text.services.audio_io import load_audio
from simple_audio_to_text.services.devices import refresh_sources
from simple_audio_to_text.services.postprocess import prepare_audio
from simple_audio_to_text.services.settings import AppSettings


def main() -> None:
    path = Path("dist-preview") / "tone.wav"
    path.parent.mkdir(exist_ok=True)
    sr = 16000
    tone = (0.2 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, sr, endpoint=False))).astype(np.float32)
    sf.write(path, tone, sr)
    loaded = load_audio(path)
    prepared = prepare_audio(loaded, AppSettings())
    mics, apps = refresh_sources()
    print(f"audio={loaded.size} prepared={prepared.size} mics={len(mics)} apps={len(apps)}")
    for item in mics[:3]:
        print("mic", item.title)
    for item in apps[:5]:
        print("app", item.title, item.kind)


if __name__ == "__main__":
    main()
