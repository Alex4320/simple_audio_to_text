#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo python
    return
  fi
  echo "Python 3.10+ not found. Install python3 and python3-venv." >&2
  exit 1
}

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating virtual environment in .venv ..."
  "$(find_python)" -m venv .venv
fi

echo "Installing application and PyInstaller ..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . pyinstaller

echo "Building dist/SpeechToText ..."
.venv/bin/python -m PyInstaller simple_audio_to_text.spec --noconfirm

target="dist/SpeechToText/SpeechToText"
if [[ ! -x "$target" ]]; then
  echo "Build finished but $target was not created" >&2
  exit 1
fi

echo "Done: $target"
echo "Copy the whole dist/SpeechToText folder if you move the app."
