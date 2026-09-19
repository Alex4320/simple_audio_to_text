from __future__ import annotations

import locale
import os
import sys

UI_LANGUAGES = ("auto", "ru", "en")

_STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        "app.title": "Speech to Text",
        "common.back": "Назад",
        "common.copy": "Копировать",
        "common.export": "Экспорт",
        "common.start": "Начать",
        "common.stop": "Стоп",
        "common.pause": "Пауза",
        "common.resume": "Продолжить",
        "common.settings": "Настройки",
        "common.quit": "Выход",
        "tray.show": "Показать окно",
        "tray.tooltip": "Speech to Text — локальное распознавание речи",
        "common.recording": "Идёт запись",
        "common.recording_level": "Идёт запись · полоска уровня должна двигаться",
        "common.refresh": "Обновить список",
        "common.mic": "Микрофон",
        "common.app": "Приложение",
        "common.device_app": "Устройство / приложение",
        "badge.pause": "ПАУЗА",
        "home.kicker": "ЛОКАЛЬНО НА ЭТОМ КОМПЬЮТЕРЕ",
        "home.title": "Речь в текст",
        "home.subtitle": "Аудио, эфир, запись или видео. Распознавание работает офлайн.",
        "home.file_title": "Audio to text",
        "home.file_sub": "Аудиофайл с диска сразу в текст.",
        "home.live_title": "Live to text",
        "home.live_sub": "Микрофон или приложение в эфире.",
        "home.save_title": "Save audio",
        "home.save_sub": "Запись в WAV, MP3, FLAC.",
        "home.video_title": "Video to audio",
        "home.video_sub": "Видео в аудио, можно сразу в текст.",
        "home.footnote": "Windows и Linux · без облака · видео можно сразу расшифровать в текст",
        "file.title": "Audio to text",
        "file.meta_empty": "Файл ещё не выбран",
        "file.add": "Добавить файл",
        "file.run": "Распознать",
        "file.placeholder": "Здесь появится текст после распознавания.",
        "file.drop": "Перетащите аудио сюда или нажмите «Добавить файл»",
        "file.pick": "Добавить аудио",
        "file.filter": "Аудио",
        "file.bad_format": "Этот аудиоформат не поддерживается",
        "file.preparing": "Готовлю распознавание…",
        "file.done": "Готово",
        "dialog.file": "Файл",
        "live.title": "Live to text",
        "live.status": "Выберите «Конференция» или микрофон, затем нажмите «Начать».",
        "live.placeholder": "Живой текст появится здесь.",
        "live.need_source": "Сначала нажмите «Конференция» или микрофон в списке",
        "live.writing": "Пишу: {title}",
        "live.listening": "Слушаю…",
        "live.finishing": "Завершаю и обрабатываю…",
        "live.stopped": "Запись остановлена",
        "dialog.record": "Запись",
        "record.title": "Save audio",
        "record.status": "Выберите микрофон или приложение, затем нажмите «Начать».",
        "record.need_source": "Сначала нажмите микрофон или устройство в списке",
        "record.new": "Новая запись",
        "record.meta_empty": "Фрагментов нет. Остановите запись и нажмите «Начать» снова — всё склеится в один файл.",
        "record.meta_running": "Фрагментов: {count}{extra}. После стопа можно дописать — файл останется одним.",
        "record.meta_running_extra": " · пишется ещё один фрагмент",
        "record.meta_ready": "Фрагментов: {count} · {clock}. Нажмите «Продолжить», чтобы дописать в ту же запись, или «Экспорт».",
        "record.saving": "Сохраняю фрагмент…",
        "record.added": "Фрагмент добавлен. Можно экспортировать или дописать ещё.",
        "record.empty_take": "Фрагмент пустой. Нажмите «Начать» и проверьте источник.",
        "record.reset_title": "Новая запись",
        "record.reset_body": "Сбросить текущие фрагменты? Экспортированный файл уже не затронется.",
        "record.reset_status": "Новая запись. Выберите источник и нажмите «Начать».",
        "record.need_audio": "Сначала запишите звук.",
        "record.saved": "Сохранено: {name}",
        "record.writing": "Пишу…",
        "video.title": "Video to audio",
        "video.drop": "Перетащите видео сюда или нажмите «Добавить видео»",
        "video.meta_empty": "Видео ещё не выбрано",
        "video.transcribe": "Транскрибация текста",
        "video.transcribe_tip": "После извлечения аудио распознать речь теми же настройками, что и в Audio to text.",
        "video.add": "Добавить видео",
        "video.run": "Конвертировать",
        "video.placeholder": "Если включить транскрибацию, здесь появится текст.",
        "video.copy": "Копировать текст",
        "video.export": "Экспорт текста",
        "video.pick": "Добавить видео",
        "video.filter": "Видео",
        "video.bad_format": "Этот видеоформат не поддерживается",
        "video.preparing": "Готовлю конвертацию…",
        "video.done_text": "Аудио: {name} · текст готов",
        "video.done": "Аудио сохранено: {name}",
        "video.save_audio": "Сохранить аудио",
        "dialog.video": "Видео",
        "dialog.export": "Экспорт",
        "dialog.export_audio": "Экспорт аудио",
        "settings.title": "Настройки",
        "settings.hint": "Тяжёлые модели точнее, но занимают больше памяти и скачиваются один раз.",
        "settings.ui_language": "Язык интерфейса",
        "settings.ui_language_sub": "По умолчанию берётся язык системы: русский или английский.",
        "settings.ui_auto": "Как в системе",
        "settings.ui_ru": "Русский",
        "settings.ui_en": "English",
        "settings.model": "Модель Whisper",
        "settings.model_sub": "Цифры — примерный объём видеопамяти (CUDA) и оперативной памяти (CPU).",
        "settings.speech": "Язык распознавания",
        "settings.speech_sub": "Для смеси русского и английского лучше выбрать язык явно.",
        "settings.device": "Устройство",
        "settings.device_sub": "CUDA ускоряет large-модели. CPU справится с tiny–medium.",
        "settings.gpu": "Видеокарта",
        "settings.gpu_sub": "Какая GPU будет считать распознавание.",
        "settings.no_gpu": "NVIDIA GPU не найдена",
        "settings.speech_auto": "Автоопределение",
        "settings.speech_ru": "Русский",
        "settings.speech_en": "English",
        "settings.model.tiny": "tiny · быстро",
        "settings.model.base": "base · баланс",
        "settings.model.small": "small · точнее",
        "settings.model.medium": "medium · тяжелее",
        "settings.model.large-v2": "large-v2 · очень точно",
        "settings.model.large-v3": "large-v3 · максимум качества",
        "settings.model.large-v3-turbo": "large-v3-turbo · large быстрее",
        "settings.model.distil-large-v3": "distil-large-v3 · large легче",
        "settings.dev.auto": "Авто · GPU если есть",
        "settings.dev.cpu": "CPU",
        "settings.dev.cuda": "CUDA · GPU NVIDIA",
        "settings.fillers": "Удаление слов-паразитов",
        "settings.fillers_sub": "Убирает «ну», «типа», um, uh и похожие вставки.",
        "settings.speakers": "Разделение спикеров",
        "settings.speakers_sub": "Подписывает реплики как Спикер 1, Спикер 2…",
        "settings.denoise": "Шумоподавление",
        "settings.denoise_sub": "Приглушает фон перед распознаванием.",
        "settings.silence": "Удаление тишины",
        "settings.silence_sub": "Сжимает длинные паузы, чтобы модель меньше галлюцинировала.",
        "settings.normalize": "Нормализация громкости",
        "settings.normalize_sub": "Выравнивает тихие записи перед распознаванием.",
        "settings.timestamps": "Таймкоды в тексте",
        "settings.timestamps_sub": "Пишет время начала каждой фразы.",
        "settings.cpu_ram": "Для {model} нужно примерно {ram} ГБ ОЗУ. Видеопамять не используется.",
        "settings.cpu_now": "Сейчас используется CPU. GPU не задействована.",
        "settings.no_gpu_hint": "Для {model} нужно примерно {vram} ГБ VRAM или {ram} ГБ ОЗУ. GPU не найдена — будет CPU.",
        "settings.no_gpu_status": "GPU не видна: нет NVIDIA-драйвера или CTranslate2 собран без CUDA.",
        "settings.low_vram": "Для {model} нужно примерно {vram} ГБ VRAM. У {gpu} около {available} ГБ — может не хватить. Возьмите модель легче или CPU ({ram} ГБ ОЗУ).",
        "settings.ok_vram": "Для {model} нужно примерно {vram} ГБ VRAM. У {gpu} около {available} ГБ — должно хватить. На CPU той же модели нужно около {ram} ГБ ОЗУ.",
        "settings.generic_mem": "Для {model} нужно примерно {vram} ГБ VRAM или {ram} ГБ ОЗУ.",
        "settings.will_use": "Будет использоваться: {compute}",
        "settings.mem_label": "~{vram} ГБ VRAM / ~{ram} ГБ ОЗУ",
        "worker.read_file": "Читаю файл…",
        "worker.file_fail": "Не удалось распознать файл",
        "worker.extract": "Извлекаю аудио из видео…",
        "worker.read_extracted": "Читаю извлечённое аудио…",
        "worker.video_fail": "Не удалось обработать видео",
        "worker.load_model": "Загружаю модель на {runtime}…",
        "worker.model_fail": "Не удалось загрузить модель",
        "worker.listen": "Слушаю: {title} · {runtime}",
        "worker.listen_short": "Слушаю: {title}",
        "worker.quiet": "Звук не слышен. Для Zoom выберите «Конференция» и проверьте, что она играет в текущие наушники или колонки.",
        "worker.recognize": "Распознаю…",
        "worker.speakers": "Делю реплики по спикерам…",
        "worker.live_fail": "Ошибка живой записи",
        "worker.record": "Пишу: {title}",
        "worker.record_fail": "Не удалось писать звук",
        "worker.empty_take": "Фрагмент пустой — звук не был слышен.",
        "asr.cuda_missing": "CUDA недоступна. Нужны NVIDIA GPU и CTranslate2 с поддержкой CUDA, либо выберите CPU в настройках.",
        "asr.cuda_off": "CUDA недоступна · модель {model}",
        "asr.cpu": "CPU · модель {model}",
        "asr.cuda": "CUDA · модель {model}",
        "asr.gpu": "{name} · модель {model}",
        "asr.gb": "ГБ",
        "asr.check_model": "Проверяю модель {name}…",
        "asr.open_model": "Открываю {name} в память…",
        "asr.model_ready": "Модель {name} готова",
        "asr.too_short": "Слишком мало звука для распознавания",
        "asr.unknown_model": "Неизвестная модель: {name}",
        "asr.recognize_on": "Распознаю на {runtime}…",
        "progress.gb": "ГБ",
        "progress.mb": "МБ",
        "progress.kb": "КБ",
        "progress.b": "Б",
        "progress.speed": "{size}/с",
        "progress.load": "Загрузка модели: {current} / {total} · {percent}%",
        "progress.load_partial": "Загрузка модели: {current}",
        "devices.default": "по умолчанию",
        "devices.active": "активен",
        "devices.mic": "микрофон",
        "devices.system": "Системный звук",
        "devices.app": "Приложение",
        "devices.system_detail": "то, что сейчас слышно из колонок или наушников",
        "devices.output": "выходной сигнал компьютера",
        "devices.playback": "воспроизведение",
        "devices.stream": "Поток {index}",
        "capture.loopback": "Не удалось открыть запись системного звука. Проверьте, что конференция играет в текущие колонки или наушники.",
        "capture.no_loop": "Не удалось найти устройство для записи системного звука.",
        "capture.no_loopback_dev": "Нет loopback-устройства для этого выхода. Выберите «Системный звук» или приложение, которое сейчас играет.",
        "capture.open": "Не удалось открыть источник звука",
        "io.read_fail": "Не удалось прочитать аудио из файла",
        "io.no_track": "В файле нет звуковой дорожки",
        "export.no_audio": "Нет записанного звука",
        "export.unknown": "Неизвестный формат: {suffix}",
        "export.save_fail": "Не удалось сохранить {suffix}",
        "export.extract_fail": "Не удалось извлечь аудио из видео",
        "export.heading": "Транскрипт",
        "export.speaker": "Спикер {n}",
        "export.filter_txt": "Текст (*.txt)",
        "export.filter_srt": "Субтитры SubRip (*.srt)",
        "export.filter_vtt": "WebVTT (*.vtt)",
        "export.filter_json": "JSON (*.json)",
        "export.filter_md": "Markdown (*.md)",
        "export.filter_docx": "Word (*.docx)",
        "export.filter_wav": "WAV (*.wav)",
        "export.filter_mp3": "MP3 (*.mp3)",
        "export.filter_flac": "FLAC (*.flac)",
        "export.filter_ogg": "OGG Vorbis (*.ogg)",
        "export.filter_m4a": "M4A AAC (*.m4a)",
        "export.filter_opus": "Opus (*.opus)",
    },
    "en": {
        "app.title": "Speech to Text",
        "common.back": "Back",
        "common.copy": "Copy",
        "common.export": "Export",
        "common.start": "Start",
        "common.stop": "Stop",
        "common.pause": "Pause",
        "common.resume": "Resume",
        "common.settings": "Settings",
        "common.quit": "Quit",
        "tray.show": "Show window",
        "tray.tooltip": "Speech to Text — offline speech recognition",
        "common.recording": "Recording",
        "common.recording_level": "Recording · the level meter should move",
        "common.refresh": "Refresh list",
        "common.mic": "Microphone",
        "common.app": "Application",
        "common.device_app": "Device / app",
        "badge.pause": "PAUSE",
        "home.kicker": "LOCAL ON THIS COMPUTER",
        "home.title": "Speech to text",
        "home.subtitle": "Audio, live, recording, or video. Recognition runs offline.",
        "home.file_title": "Audio to text",
        "home.file_sub": "Turn an audio file into text.",
        "home.live_title": "Live to text",
        "home.live_sub": "Microphone or app, transcribed live.",
        "home.save_title": "Save audio",
        "home.save_sub": "Record to WAV, MP3, FLAC.",
        "home.video_title": "Video to audio",
        "home.video_sub": "Extract audio, optionally transcribe.",
        "home.footnote": "Windows and Linux · offline · video can be transcribed too",
        "file.title": "Audio to text",
        "file.meta_empty": "No file selected yet",
        "file.add": "Add file",
        "file.run": "Transcribe",
        "file.placeholder": "The transcript will appear here.",
        "file.drop": "Drop audio here or click “Add file”",
        "file.pick": "Add audio",
        "file.filter": "Audio",
        "file.bad_format": "This audio format is not supported",
        "file.preparing": "Preparing transcription…",
        "file.done": "Done",
        "dialog.file": "File",
        "live.title": "Live to text",
        "live.status": "Select a meeting or microphone, then press Start.",
        "live.placeholder": "Live text will appear here.",
        "live.need_source": "Select a meeting or microphone in the list first",
        "live.writing": "Recording: {title}",
        "live.listening": "Listening…",
        "live.finishing": "Finishing and processing…",
        "live.stopped": "Recording stopped",
        "dialog.record": "Recording",
        "record.title": "Save audio",
        "record.status": "Select a microphone or app, then press Start.",
        "record.need_source": "Select a microphone or device in the list first",
        "record.new": "New recording",
        "record.meta_empty": "No takes yet. Stop, then press Start again — everything joins into one file.",
        "record.meta_running": "Takes: {count}{extra}. After Stop you can append — it stays one file.",
        "record.meta_running_extra": " · recording another take",
        "record.meta_ready": "Takes: {count} · {clock}. Press Resume to append, or Export.",
        "record.saving": "Saving take…",
        "record.added": "Take added. Export it or record more.",
        "record.empty_take": "Empty take. Press Start and check the source.",
        "record.reset_title": "New recording",
        "record.reset_body": "Discard the current takes? Already exported files stay as they are.",
        "record.reset_status": "New recording. Pick a source and press Start.",
        "record.need_audio": "Record some audio first.",
        "record.saved": "Saved: {name}",
        "record.writing": "Recording…",
        "video.title": "Video to audio",
        "video.drop": "Drop a video here or click “Add video”",
        "video.meta_empty": "No video selected yet",
        "video.transcribe": "Transcribe text",
        "video.transcribe_tip": "After extracting audio, also transcribe it with the same settings as Audio to text.",
        "video.add": "Add video",
        "video.run": "Convert",
        "video.placeholder": "If transcription is on, the text will appear here.",
        "video.copy": "Copy text",
        "video.export": "Export text",
        "video.pick": "Add video",
        "video.filter": "Video",
        "video.bad_format": "This video format is not supported",
        "video.preparing": "Preparing conversion…",
        "video.done_text": "Audio: {name} · transcript ready",
        "video.done": "Audio saved: {name}",
        "video.save_audio": "Save audio",
        "dialog.video": "Video",
        "dialog.export": "Export",
        "dialog.export_audio": "Export audio",
        "settings.title": "Settings",
        "settings.hint": "Larger models are more accurate, use more memory, and download once.",
        "settings.ui_language": "Interface language",
        "settings.ui_language_sub": "Default follows the system: Russian or English.",
        "settings.ui_auto": "System default",
        "settings.ui_ru": "Русский",
        "settings.ui_en": "English",
        "settings.model": "Whisper model",
        "settings.model_sub": "Numbers are approximate VRAM (CUDA) and RAM (CPU).",
        "settings.speech": "Recognition language",
        "settings.speech_sub": "For mixed Russian and English, pick a language explicitly.",
        "settings.device": "Device",
        "settings.device_sub": "CUDA speeds up large models. CPU is fine for tiny–medium.",
        "settings.gpu": "Graphics card",
        "settings.gpu_sub": "Which GPU will run recognition.",
        "settings.no_gpu": "No NVIDIA GPU found",
        "settings.speech_auto": "Auto detect",
        "settings.speech_ru": "Russian",
        "settings.speech_en": "English",
        "settings.model.tiny": "tiny · fast",
        "settings.model.base": "base · balanced",
        "settings.model.small": "small · more accurate",
        "settings.model.medium": "medium · heavier",
        "settings.model.large-v2": "large-v2 · very accurate",
        "settings.model.large-v3": "large-v3 · best quality",
        "settings.model.large-v3-turbo": "large-v3-turbo · large, faster",
        "settings.model.distil-large-v3": "distil-large-v3 · lighter large",
        "settings.dev.auto": "Auto · GPU if available",
        "settings.dev.cpu": "CPU",
        "settings.dev.cuda": "CUDA · NVIDIA GPU",
        "settings.fillers": "Remove filler words",
        "settings.fillers_sub": "Drops “um”, “uh”, and similar fillers.",
        "settings.speakers": "Split speakers",
        "settings.speakers_sub": "Labels lines as Speaker 1, Speaker 2…",
        "settings.denoise": "Denoise",
        "settings.denoise_sub": "Reduces background noise before recognition.",
        "settings.silence": "Remove silence",
        "settings.silence_sub": "Shortens long pauses so the model hallucinates less.",
        "settings.normalize": "Normalize volume",
        "settings.normalize_sub": "Evens out quiet recordings before recognition.",
        "settings.timestamps": "Timestamps in text",
        "settings.timestamps_sub": "Writes the start time of each phrase.",
        "settings.cpu_ram": "{model} needs about {ram} GB of RAM. VRAM is not used.",
        "settings.cpu_now": "Using CPU. The GPU is idle.",
        "settings.no_gpu_hint": "{model} needs about {vram} GB VRAM or {ram} GB RAM. No GPU found — CPU will be used.",
        "settings.no_gpu_status": "No GPU visible: missing NVIDIA driver or CTranslate2 built without CUDA.",
        "settings.low_vram": "{model} needs about {vram} GB VRAM. {gpu} has about {available} GB — it may not fit. Pick a lighter model or CPU ({ram} GB RAM).",
        "settings.ok_vram": "{model} needs about {vram} GB VRAM. {gpu} has about {available} GB — that should be enough. The same model on CPU needs about {ram} GB RAM.",
        "settings.generic_mem": "{model} needs about {vram} GB VRAM or {ram} GB RAM.",
        "settings.will_use": "Will use: {compute}",
        "settings.mem_label": "~{vram} GB VRAM / ~{ram} GB RAM",
        "worker.read_file": "Reading file…",
        "worker.file_fail": "Could not transcribe the file",
        "worker.extract": "Extracting audio from video…",
        "worker.read_extracted": "Reading extracted audio…",
        "worker.video_fail": "Could not process the video",
        "worker.load_model": "Loading the model on {runtime}…",
        "worker.model_fail": "Could not load the model",
        "worker.listen": "Listening: {title} · {runtime}",
        "worker.listen_short": "Listening: {title}",
        "worker.quiet": "No sound heard. For Zoom pick “Conference” and make sure it plays to the current headphones or speakers.",
        "worker.recognize": "Transcribing…",
        "worker.speakers": "Splitting speakers…",
        "worker.live_fail": "Live recording error",
        "worker.record": "Recording: {title}",
        "worker.record_fail": "Could not record audio",
        "worker.empty_take": "Empty take — no sound was heard.",
        "asr.cuda_missing": "CUDA is unavailable. You need an NVIDIA GPU and CTranslate2 with CUDA, or choose CPU in settings.",
        "asr.cuda_off": "CUDA unavailable · {model} model",
        "asr.cpu": "CPU · {model} model",
        "asr.cuda": "CUDA · {model} model",
        "asr.gpu": "{name} · {model} model",
        "asr.gb": "GB",
        "asr.check_model": "Checking {name} model…",
        "asr.open_model": "Loading {name} into memory…",
        "asr.model_ready": "{name} model is ready",
        "asr.too_short": "Not enough audio to transcribe",
        "asr.unknown_model": "Unknown model: {name}",
        "asr.recognize_on": "Transcribing on {runtime}…",
        "progress.gb": "GB",
        "progress.mb": "MB",
        "progress.kb": "KB",
        "progress.b": "B",
        "progress.speed": "{size}/s",
        "progress.load": "Downloading model: {current} / {total} · {percent}%",
        "progress.load_partial": "Downloading model: {current}",
        "devices.default": "default",
        "devices.active": "active",
        "devices.mic": "microphone",
        "devices.system": "System audio",
        "devices.app": "Application",
        "devices.system_detail": "what you currently hear from speakers or headphones",
        "devices.output": "computer output",
        "devices.playback": "playback",
        "devices.stream": "Stream {index}",
        "capture.loopback": "Could not open system audio. Make sure the meeting plays to the current speakers or headphones.",
        "capture.no_loop": "Could not find a device for system audio.",
        "capture.no_loopback_dev": "No loopback device for this output. Choose System audio or an app that is playing now.",
        "capture.open": "Could not open the audio source",
        "io.read_fail": "Could not read audio from the file",
        "io.no_track": "The file has no audio track",
        "export.no_audio": "No recorded audio",
        "export.unknown": "Unknown format: {suffix}",
        "export.save_fail": "Could not save {suffix}",
        "export.extract_fail": "Could not extract audio from the video",
        "export.heading": "Transcript",
        "export.speaker": "Speaker {n}",
        "export.filter_txt": "Text (*.txt)",
        "export.filter_srt": "SubRip subtitles (*.srt)",
        "export.filter_vtt": "WebVTT (*.vtt)",
        "export.filter_json": "JSON (*.json)",
        "export.filter_md": "Markdown (*.md)",
        "export.filter_docx": "Word (*.docx)",
        "export.filter_wav": "WAV (*.wav)",
        "export.filter_mp3": "MP3 (*.mp3)",
        "export.filter_flac": "FLAC (*.flac)",
        "export.filter_ogg": "OGG Vorbis (*.ogg)",
        "export.filter_m4a": "M4A AAC (*.m4a)",
        "export.filter_opus": "Opus (*.opus)",
    },
}

_current: str | None = None


def _looks_russian(value: str | None) -> bool:
    if not value:
        return False
    text = value.replace("-", "_").lower()
    return text.startswith("ru") or "russian" in text or "русский" in text


def system_ui_language() -> str:
    env_keys = ("LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE")
    for key in env_keys:
        if _looks_russian(os.environ.get(key)):
            return "ru"
    try:
        for item in locale.getlocale():
            if _looks_russian(item):
                return "ru"
    except Exception:
        pass
    try:
        for item in locale.getdefaultlocale():
            if _looks_russian(item):
                return "ru"
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id & 0xFF == 0x19:
                return "ru"
        except Exception:
            pass
    try:
        from PySide6.QtCore import QLocale

        system = QLocale.system()
        if system.language() == QLocale.Language.Russian:
            return "ru"
        for name in system.uiLanguages():
            if _looks_russian(name):
                return "ru"
    except Exception:
        pass
    return "en"


def resolve_ui_language(preference: str | None) -> str:
    if preference in {"ru", "en"}:
        return preference
    return system_ui_language()


def current_ui_language() -> str:
    global _current
    if _current is None:
        _current = system_ui_language()
    return _current


def set_ui_language(preference: str | None) -> str:
    global _current
    _current = resolve_ui_language(preference)
    try:
        from PySide6.QtCore import QLocale

        if _current == "ru":
            QLocale.setDefault(QLocale(QLocale.Language.Russian))
        else:
            QLocale.setDefault(QLocale(QLocale.Language.English))
    except Exception:
        pass
    return _current


def t(key: str, **kwargs) -> str:
    lang = current_ui_language()
    text = _STRINGS.get(lang, {}).get(key) or _STRINGS["en"].get(key) or key
    if kwargs:
        return text.format(**kwargs)
    return text


def transcript_export_filter() -> str:
    return ";;".join(
        [
            t("export.filter_txt"),
            t("export.filter_srt"),
            t("export.filter_vtt"),
            t("export.filter_json"),
            t("export.filter_md"),
            t("export.filter_docx"),
        ]
    )


def audio_export_filter() -> str:
    return ";;".join(
        [
            t("export.filter_wav"),
            t("export.filter_mp3"),
            t("export.filter_flac"),
            t("export.filter_ogg"),
            t("export.filter_m4a"),
            t("export.filter_opus"),
        ]
    )
