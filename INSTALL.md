# Install

[English](#english) · [Русский](#русский)

How to install Speech to Text from this repository: run from source or build a standalone folder.

Как поставить Speech to Text из файлов репозитория: запуск из исходников или сборка автономной папки.

---

## English

### 1. Get the files

**Git**

```bash
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
```

**ZIP from GitHub**

1. Open the repository on GitHub.
2. **Code → Download ZIP**.
3. Unpack it.
4. Open a terminal in the unpacked folder (`simple_audio_to_text-main` or similar).

You need these paths:

| Path | Role |
| --- | --- |
| `pyproject.toml` | Python package and dependencies |
| `src/simple_audio_to_text/` | Application code |
| `scripts/run.ps1` / `scripts/run.sh` | Start from source |
| `scripts/build_windows.ps1` | Windows build |
| `scripts/build_linux.sh` | Linux build |
| `simple_audio_to_text.spec` | PyInstaller recipe |

### 2. Prerequisites

#### Both platforms

- **Python 3.10–3.13** on `PATH` (`python --version` or `python3 --version`)
- Internet for the first `pip install` and the first Whisper model download
- Optional NVIDIA GPU + current driver if you want CUDA

#### Windows

- Windows 10 or 11
- [Python for Windows](https://www.python.org/downloads/) with **Add python.exe to PATH**
- For a packaged `.exe`: [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

#### Linux

Desktop audio stack plus PortAudio headers (Debian / Ubuntu):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip \
  portaudio19-dev pulseaudio-utils
```

Fedora:

```bash
sudo dnf install python3 python3-pip portaudio-devel pulseaudio-utils
```

PipeWire setups usually still expose PulseAudio-compatible tools.

### 3. Create a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip install -e .
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e .
```

This reads `pyproject.toml` and installs PySide6, faster-whisper, audio libraries, and the `simple-audio-to-text` command.

Developers who also want tests:

```bash
# Windows
.\.venv\Scripts\pip install -e . pytest

# Linux
.venv/bin/pip install -e . pytest
.venv/bin/python -m pytest
```

### 4. Run from the repository

Windows:

```powershell
.\scripts\run.ps1
```

or:

```powershell
.\.venv\Scripts\python.exe -m simple_audio_to_text
```

Linux:

```bash
chmod +x scripts/run.sh scripts/build_linux.sh
./scripts/run.sh
```

or:

```bash
.venv/bin/python -m simple_audio_to_text
```

The window title is **Speech to Text**. Interface language follows the OS (Russian or English) until you change it in Settings.

### 5. First transcription

The first time you transcribe, the selected Whisper model is downloaded into a `models` folder next to the app. That can take several minutes and needs disk space.

Typical model cache:

- From source: `<repo>/models`
- Packaged build: `SpeechToText/models` next to `SpeechToText.exe` / `SpeechToText`

Start with **base** or **small**. Larger models are more accurate and need more RAM / VRAM.

### 6. Build a standalone app

The build scripts create a venv if needed, install dependencies and PyInstaller, then pack `dist/SpeechToText/`.

Windows (PowerShell):

```powershell
.\scripts\build_windows.ps1
```

Result: `dist\SpeechToText\SpeechToText.exe`

Copy the whole `SpeechToText` folder if you move the app. The `.exe` is not a single-file build.

If `SpeechToText.exe` is already running, the script closes it so files can be overwritten.

Linux:

```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

Result: `dist/SpeechToText/SpeechToText`

```bash
./dist/SpeechToText/SpeechToText
```

### 7. GPU (optional)

1. Install a current NVIDIA driver.
2. In the app: **Settings → Device → CUDA** (or Auto).
3. Pick the GPU if several are listed.

If CUDA is missing, the app stays on CPU. You do not need a GPU for `tiny`–`medium`.

### Troubleshooting

| Problem | What to try |
| --- | --- |
| `python` not found | Reinstall Python and enable PATH, or use `py -3.12` on Windows / `python3` on Linux |
| `pip install` fails on Linux | Install `portaudio19-dev` (or `portaudio-devel`) and retry |
| App starts, no microphones | Allow microphone access in the OS; on Linux check PulseAudio / PipeWire |
| Zoom / meeting is silent | Choose the meeting or **System audio**, and make sure it plays to the current speakers or headphones |
| First run is slow | The model is downloading. Watch the progress bar |
| Packaged Windows app will not start | Install the VC++ Redistributable |
| Build cannot overwrite files | Close `SpeechToText` and run the script again |

### Uninstall

- **From source:** delete the cloned folder, the `.venv` inside it, and `<repo>/models` if you want to drop downloaded models.
- **Settings:** remove the `SimpleAudioToText` config folder (`%APPDATA%` on Windows, `~/.config` on Linux).
- **Packaged build:** delete the `SpeechToText` folder, including `models` next to the executable.

---

## Русский

### 1. Получить файлы

**Git**

```bash
git clone https://github.com/Alex4320/simple_audio_to_text.git
cd simple_audio_to_text
```

**ZIP с GitHub**

1. Откройте репозиторий на GitHub.
2. **Code → Download ZIP**.
3. Распакуйте архив.
4. Откройте терминал в распакованной папке (`simple_audio_to_text-main` или похожее имя).

Нужны такие пути:

| Путь | Зачем |
| --- | --- |
| `pyproject.toml` | Пакет Python и зависимости |
| `src/simple_audio_to_text/` | Код приложения |
| `scripts/run.ps1` / `scripts/run.sh` | Запуск из исходников |
| `scripts/build_windows.ps1` | Сборка на Windows |
| `scripts/build_linux.sh` | Сборка на Linux |
| `simple_audio_to_text.spec` | Рецепт PyInstaller |

### 2. Что должно быть установлено

#### Обе платформы

- **Python 3.10–3.13** в `PATH` (`python --version` или `python3 --version`)
- Интернет для первого `pip install` и первой загрузки модели Whisper
- По желанию NVIDIA GPU и актуальный драйвер, если нужен CUDA

#### Windows

- Windows 10 или 11
- [Python для Windows](https://www.python.org/downloads/) с галочкой **Add python.exe to PATH**
- Для готового `.exe`: [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

#### Linux

Звук рабочего стола и заголовки PortAudio (Debian / Ubuntu):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip \
  portaudio19-dev pulseaudio-utils
```

Fedora:

```bash
sudo dnf install python3 python3-pip portaudio-devel pulseaudio-utils
```

На PipeWire обычно остаются совместимые с PulseAudio утилиты.

### 3. Виртуальное окружение

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip install -e .
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e .
```

Команда читает `pyproject.toml` и ставит PySide6, faster-whisper, аудиобиблиотеки и команду `simple-audio-to-text`.

Если нужны тесты:

```bash
# Windows
.\.venv\Scripts\pip install -e . pytest

# Linux
.venv/bin/pip install -e . pytest
.venv/bin/python -m pytest
```

### 4. Запуск из репозитория

Windows:

```powershell
.\scripts\run.ps1
```

или:

```powershell
.\.venv\Scripts\python.exe -m simple_audio_to_text
```

Linux:

```bash
chmod +x scripts/run.sh scripts/build_linux.sh
./scripts/run.sh
```

или:

```bash
.venv/bin/python -m simple_audio_to_text
```

Заголовок окна — **Speech to Text**. Язык интерфейса берётся из системы (русский или английский), пока его не сменить в настройках.

### 5. Первое распознавание

При первой расшифровке выбранная модель Whisper скачивается в папку `models` рядом с приложением. Это может занять несколько минут и требует места на диске.

Обычное место кэша моделей:

- Из исходников: `<репозиторий>/models`
- Готовая сборка: `SpeechToText/models` рядом с `SpeechToText.exe` / `SpeechToText`

Начните с **base** или **small**. Более тяжёлые модели точнее и едят больше ОЗУ / VRAM.

### 6. Сборка автономного приложения

Скрипты сами создадут venv при необходимости, поставят зависимости и PyInstaller, затем соберут `dist/SpeechToText/`.

Windows (PowerShell):

```powershell
.\scripts\build_windows.ps1
```

Результат: `dist\SpeechToText\SpeechToText.exe`

Если переносите приложение, копируйте всю папку `SpeechToText`. Это не один файл.

Если `SpeechToText.exe` уже запущен, скрипт закроет его, чтобы можно было перезаписать файлы.

Linux:

```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

Результат: `dist/SpeechToText/SpeechToText`

```bash
./dist/SpeechToText/SpeechToText
```

### 7. GPU (по желанию)

1. Поставьте актуальный драйвер NVIDIA.
2. В приложении: **Настройки → Устройство → CUDA** (или Авто).
3. Если карт несколько, выберите нужную.

Если CUDA нет, приложение останется на CPU. Для `tiny`–`medium` видеокарта не обязательна.

### Если что-то пошло не так

| Проблема | Что сделать |
| --- | --- |
| `python` не найден | Переустановите Python с PATH или вызовите `py -3.12` на Windows / `python3` на Linux |
| `pip install` падает на Linux | Поставьте `portaudio19-dev` (или `portaudio-devel`) и повторите |
| Окно открылось, микрофонов нет | Разрешите микрофон в системе; на Linux проверьте PulseAudio / PipeWire |
| Zoom / конференция молчит | Выберите конференцию или **Системный звук** и проверьте, что она играет в текущие колонки или наушники |
| Первый запуск долгий | Качается модель. Смотрите полоску прогресса |
| Готовое приложение на Windows не стартует | Поставьте VC++ Redistributable |
| Сборка не может перезаписать файлы | Закройте `SpeechToText` и запустите скрипт снова |

### Удаление

- **Из исходников:** удалите папку репозитория вместе с `.venv` и при желании `<репозиторий>/models`.
- **Настройки:** удалите каталог `SimpleAudioToText` в `%APPDATA%` на Windows или в `~/.config` на Linux.
- **Готовая сборка:** удалите папку `SpeechToText`, включая `models` рядом с exe.
