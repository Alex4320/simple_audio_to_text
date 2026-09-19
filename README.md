# Speech to Text

<p align="center">
  <img src="assets/logo.png" alt="Speech to Text" width="128" height="128">
</p>

[English](#english) · [Русский](#русский)

Offline speech-to-text for **Windows** and **Linux**. Audio files, live capture, recordings, and video — all on this computer. No cloud.

Локальное распознавание речи для **Windows** и **Linux**. Аудио, эфир, запись и видео — всё на этом компьютере. Без облака.

<p>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Windows and Linux" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-111827">
  <img alt="Offline" src="https://img.shields.io/badge/recognition-offline-16a34a">
  <img alt="License" src="https://img.shields.io/badge/license-PolyForm%20Noncommercial-6d28d9">
</p>

---

## English

Speech to Text is a desktop app that turns speech into text with [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Models run locally (CPU or NVIDIA CUDA). The first run downloads the chosen Whisper model into the `models` folder next to the app.

### Features

| Mode | What it does |
| --- | --- |
| **Audio to text** | Drop or pick an audio file and transcribe it |
| **Live to text** | Transcribe a microphone or a playing app in real time |
| **Save audio** | Record from a mic or device, pause, append, export WAV / MP3 / FLAC / OGG / M4A / Opus |
| **Video to audio** | Extract audio from common video formats, optionally transcribe |

Also included:

- Interface in **English** or **Russian** (follows the system language by default)
- Recognition language: auto, Russian, or English
- Whisper models from `tiny` to `large-v3` / `distil-large-v3`
- CPU or NVIDIA GPU (CUDA)
- Filler-word cleanup, speaker labels, denoise, silence trim, loudness normalize, timestamps
- Transcript export: TXT, SRT, VTT, JSON, Markdown, DOCX

Nothing is uploaded. Recognition stays on the machine.

### Quick start

Full steps: **[INSTALL.md](INSTALL.md#english)**.

```powershell
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
python -m venv .venv
.\.venv\Scripts\pip install -e .
.\.venv\Scripts\python -m simple_audio_to_text
```

Linux:

```bash
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
sudo apt install portaudio19-dev pulseaudio-utils
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m simple_audio_to_text
```

Build a standalone folder:

- Windows: `.\scripts\build_windows.ps1` → `dist/SpeechToText/SpeechToText.exe`
- Linux: `./scripts/build_linux.sh` → `dist/SpeechToText/SpeechToText`

### Requirements

- Python **3.10–3.13**
- Windows 10/11 or a recent Linux desktop (PulseAudio or PipeWire)
- Optional: NVIDIA GPU + driver for CUDA
- Windows packaged builds need the [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

### Live capture

- **Windows:** the list follows the sound mixer. Recording uses the current playback path (speakers or headphones).
- **Linux:** apps come from PulseAudio / PipeWire. Capture uses the output monitor.

### License

[PolyForm Noncommercial 1.0.0](LICENSE).

You may use, study, and change this project for personal and other non-commercial purposes. **Selling the app, using it in a paid product, or other commercial use needs a separate license from the copyright holder.** That keeps the door open to monetize later without giving those rights away.

---

## Русский

Speech to Text — настольное приложение, которое переводит речь в текст через [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Модели считаются локально (CPU или NVIDIA CUDA). При первом запуске выбранная модель Whisper скачивается в папку `models` рядом с приложением.

### Возможности

| Режим | Что делает |
| --- | --- |
| **Audio to text** | Файл с диска или перетаскиванием сразу в текст |
| **Live to text** | Микрофон или приложение в эфире |
| **Save audio** | Запись с микрофона или устройства, пауза, дозапись, экспорт WAV / MP3 / FLAC / OGG / M4A / Opus |
| **Video to audio** | Аудио из видео, по желанию сразу распознать текст |

Дополнительно:

- Интерфейс на **русском** или **английском** (по умолчанию — язык системы)
- Язык распознавания: авто, русский или английский
- Модели Whisper от `tiny` до `large-v3` / `distil-large-v3`
- CPU или видеокарта NVIDIA (CUDA)
- Слова-паразиты, спикеры, шум, тишина, громкость, таймкоды
- Экспорт текста: TXT, SRT, VTT, JSON, Markdown, DOCX

В облако ничего не уходит. Распознавание остаётся на этом компьютере.

### Быстрый старт

Подробности: **[INSTALL.md](INSTALL.md#русский)**.

```powershell
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
python -m venv .venv
.\.venv\Scripts\pip install -e .
.\.venv\Scripts\python -m simple_audio_to_text
```

Linux:

```bash
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
sudo apt install portaudio19-dev pulseaudio-utils
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m simple_audio_to_text
```

Сборка автономной папки:

- Windows: `.\scripts\build_windows.ps1` → `dist/SpeechToText/SpeechToText.exe`
- Linux: `./scripts/build_linux.sh` → `dist/SpeechToText/SpeechToText`

### Требования

- Python **3.10–3.13**
- Windows 10/11 или актуальный Linux с PulseAudio / PipeWire
- По желанию: NVIDIA GPU и драйвер для CUDA
- Для готовой сборки на Windows нужен [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

### Живой звук

- **Windows:** список как в микшере. Запись идёт с текущего выхода (колонки или наушники).
- **Linux:** приложения берутся из PulseAudio / PipeWire. Пишется monitor выхода.

### Лицензия

[PolyForm Noncommercial 1.0.0](LICENSE).

Можно пользоваться, изучать и менять проект для личных и других некоммерческих целей. **Продажа приложения, использование в платном продукте и любая коммерция требуют отдельной лицензии у правообладателя.** Так можно позже монетизировать проект, не отдавая коммерческие права заранее.
