from __future__ import annotations

import sys
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "SimpleAudioToText"
APP_AUTHOR = "SimpleAudioToText"


def config_dir() -> Path:
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return config_dir() / "settings.json"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    here = Path(__file__).resolve()
    src_root = here.parents[1]
    if src_root.name == "src" and (src_root.parent / "pyproject.toml").exists():
        return src_root.parent
    return Path.cwd()


def models_dir() -> Path:
    path = app_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path
