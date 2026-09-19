from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from simple_audio_to_text.assets import app_icon
from simple_audio_to_text.services.asr import TranscriptResult
from simple_audio_to_text.services.audio_export import export_audio
from simple_audio_to_text.services.audio_io import RECORD_RATE
from simple_audio_to_text.services.export import export_transcript
from simple_audio_to_text.services.i18n import audio_export_filter, set_ui_language, t, transcript_export_filter
from simple_audio_to_text.services.settings import AppSettings, save_settings
from simple_audio_to_text.ui.file_page import FilePage
from simple_audio_to_text.ui.home_page import HomePage
from simple_audio_to_text.ui.live_page import LivePage
from simple_audio_to_text.ui.record_page import RecordPage
from simple_audio_to_text.ui.settings_page import SettingsPage
from simple_audio_to_text.ui.video_page import VideoPage
from simple_audio_to_text.ui.workers import FileWorker, LiveWorker, RecordWorker, VideoWorker


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.file_worker: FileWorker | None = None
        self.live_worker: LiveWorker | None = None
        self.record_worker: RecordWorker | None = None
        self.video_worker: VideoWorker | None = None
        self.last_result: TranscriptResult | None = None
        self._ui_language = set_ui_language(settings.ui_language)
        self._force_quit = False
        self.setWindowTitle(t("app.title"))
        icon = app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.resize(1180, 740)
        self.setMinimumSize(1000, 640)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.home = HomePage()
        self.file_page = FilePage()
        self.live_page = LivePage()
        self.record_page = RecordPage()
        self.video_page = VideoPage()
        self.settings_page = SettingsPage(settings)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.file_page)
        self.stack.addWidget(self.live_page)
        self.stack.addWidget(self.record_page)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.settings_page)

        self.home.open_file.connect(lambda: self.stack.setCurrentWidget(self.file_page))
        self.home.open_live.connect(self._open_live)
        self.home.open_record.connect(self._open_record)
        self.home.open_video.connect(lambda: self.stack.setCurrentWidget(self.video_page))
        self.home.open_settings.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        self.file_page.back.connect(self._go_home)
        self.live_page.back.connect(self._go_home)
        self.record_page.back.connect(self._go_home)
        self.video_page.back.connect(self._go_home)
        self.settings_page.back.connect(self._go_home)
        self.settings_page.changed.connect(self._settings_changed)
        self.file_page.transcribe_requested.connect(self._transcribe_file)
        self.file_page.copy_requested.connect(self._copy)
        self.file_page.save_requested.connect(self._save)
        self.live_page.start_requested.connect(self._start_live)
        self.live_page.pause_requested.connect(self._pause_live)
        self.live_page.stop_requested.connect(self._stop_live)
        self.live_page.copy_requested.connect(self._copy)
        self.live_page.save_requested.connect(self._save)
        self.record_page.start_requested.connect(self._start_record)
        self.record_page.pause_requested.connect(self._pause_record)
        self.record_page.stop_requested.connect(self._stop_record)
        self.record_page.export_requested.connect(self._export_record)
        self.record_page.clear_requested.connect(self._clear_record)
        self.video_page.convert_requested.connect(self._convert_video)
        self.video_page.copy_requested.connect(self._copy)
        self.video_page.save_requested.connect(self._save)

        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self._go_home)
        self._setup_tray()

    def _open_live(self) -> None:
        self.live_page.reload_sources()
        self.stack.setCurrentWidget(self.live_page)

    def _open_record(self) -> None:
        self.record_page.reload_sources()
        self.stack.setCurrentWidget(self.record_page)

    def _go_home(self) -> None:
        if self.live_worker and self.live_worker.isRunning():
            return
        if self.file_worker and self.file_worker.isRunning():
            return
        if self.record_worker and self.record_worker.isRunning():
            return
        if self.video_worker and self.video_worker.isRunning():
            return
        self.stack.setCurrentWidget(self.home)

    def _settings_changed(self, settings: AppSettings) -> None:
        self.settings = settings
        save_settings(settings)
        applied = set_ui_language(settings.ui_language)
        if applied != self._ui_language:
            self._ui_language = applied
            self.retranslate()

    def retranslate(self) -> None:
        self.setWindowTitle(t("app.title"))
        self.home.retranslate()
        self.file_page.retranslate()
        self.live_page.retranslate()
        self.record_page.retranslate()
        self.video_page.retranslate()
        self.settings_page.retranslate()
        self.live_page.reload_sources()
        self.record_page.reload_sources()
        self._retranslate_tray()

    def _current_settings(self) -> AppSettings:
        return replace(self.settings)

    def _transcribe_file(self, path: Path) -> None:
        if self.file_worker and self.file_worker.isRunning():
            return
        self.file_page.set_busy(True, t("file.preparing"))
        worker = FileWorker(path, self._current_settings())
        worker.status.connect(lambda text: self.file_page.set_busy(True, text))
        worker.progress.connect(self.file_page.set_load_progress)
        worker.finished_ok.connect(self._file_done)
        worker.failed.connect(self._file_failed)
        self.file_worker = worker
        worker.start()

    def _file_done(self, result: TranscriptResult) -> None:
        self.last_result = result
        self.file_page.set_text(result.text)
        self.file_page.set_busy(False, t("file.done"))

    def _file_failed(self, message: str) -> None:
        self.file_page.set_busy(False, message)
        QMessageBox.warning(self, t("dialog.file"), message)

    def _start_live(self, source) -> None:
        if self.live_worker and self.live_worker.isRunning():
            return
        self.live_page.set_running(True)
        self.live_page.set_status(t("live.writing", title=source.title))
        worker = LiveWorker(source, self._current_settings())
        worker.level.connect(self.live_page.set_level)
        worker.text_changed.connect(self.live_page.set_text)
        worker.segments_changed.connect(self._keep_live_segments)
        worker.status.connect(self.live_page.set_status)
        worker.progress.connect(self.live_page.set_load_progress)
        worker.finished_ok.connect(self._live_done)
        worker.failed.connect(self._live_failed)
        self.live_worker = worker
        worker.start()

    def _pause_live(self, paused: bool) -> None:
        if self.live_worker:
            self.live_worker.set_paused(paused)
            self.live_page.set_status(t("common.pause") if paused else t("live.listening"))

    def _stop_live(self) -> None:
        if self.live_worker:
            self.live_page.set_status(t("live.finishing"))
            self.live_worker.request_stop()

    def _keep_live_segments(self, segments) -> None:
        self.last_result = TranscriptResult(text=self.live_page.result.toPlainText(), segments=list(segments))

    def _live_done(self, result: TranscriptResult) -> None:
        self.last_result = result
        self.live_page.set_text(result.text)
        self.live_page.set_running(False)
        self.live_page.set_status(t("live.stopped"))

    def _live_failed(self, message: str) -> None:
        self.live_page.set_running(False)
        self.live_page.set_status(message)
        QMessageBox.warning(self, t("dialog.record"), message)

    def _start_record(self, source) -> None:
        if self.record_worker and self.record_worker.isRunning():
            return
        self.record_page.set_running(True)
        self.record_page.set_status(t("worker.record", title=source.title))
        worker = RecordWorker(source, RECORD_RATE)
        worker.level.connect(self.record_page.set_level)
        worker.elapsed.connect(self.record_page.set_live_seconds)
        worker.status.connect(self.record_page.set_status)
        worker.finished_ok.connect(self._record_done)
        worker.failed.connect(self._record_failed)
        self.record_worker = worker
        worker.start()

    def _pause_record(self, paused: bool) -> None:
        if self.record_worker:
            self.record_worker.set_paused(paused)
            self.record_page.set_status(t("common.pause") if paused else t("record.writing"))

    def _stop_record(self) -> None:
        if self.record_worker:
            self.record_page.set_status(t("record.saving"))
            self.record_worker.request_stop()

    def _record_done(self, audio) -> None:
        self.record_page.set_running(False)
        self.record_page.append_take(audio)
        if self.record_page.has_audio():
            self.record_page.set_status(t("record.added"))
        else:
            self.record_page.set_status(t("record.empty_take"))

    def _record_failed(self, message: str) -> None:
        self.record_page.set_running(False)
        self.record_page.set_status(message)
        QMessageBox.warning(self, t("dialog.record"), message)

    def _clear_record(self) -> None:
        if self.record_worker and self.record_worker.isRunning():
            return
        if self.record_page.has_audio():
            answer = QMessageBox.question(
                self,
                t("record.reset_title"),
                t("record.reset_body"),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.record_page.clear_takes()
        self.record_page.set_status(t("record.reset_status"))

    def _export_record(self) -> None:
        audio = self.record_page.combined_audio()
        if audio.size == 0:
            QMessageBox.information(self, t("dialog.export"), t("record.need_audio"))
            return
        path, _selected = QFileDialog.getSaveFileName(
            self,
            t("dialog.export_audio"),
            "recording.wav",
            audio_export_filter(),
        )
        if not path:
            return
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix(".wav")
        try:
            export_audio(target, audio, RECORD_RATE)
            self.record_page.set_status(t("record.saved", name=target.name))
        except Exception as exc:
            QMessageBox.warning(self, t("dialog.export"), str(exc))

    def _convert_video(self, source: Path, transcribe: bool) -> None:
        if self.video_worker and self.video_worker.isRunning():
            return
        suggested = source.with_suffix(".wav").name
        path, _selected = QFileDialog.getSaveFileName(
            self,
            t("video.save_audio"),
            suggested,
            audio_export_filter(),
        )
        if not path:
            return
        dest = Path(path)
        if not dest.suffix:
            dest = dest.with_suffix(".wav")
        self.video_page.set_busy(True, t("video.preparing"))
        worker = VideoWorker(source, dest, self._current_settings(), transcribe)
        worker.status.connect(lambda text: self.video_page.set_busy(True, text))
        worker.progress.connect(self.video_page.set_load_progress)
        worker.finished_ok.connect(self._video_done)
        worker.failed.connect(self._video_failed)
        self.video_worker = worker
        worker.start()

    def _video_done(self, result) -> None:
        if result.transcript is not None:
            self.last_result = result.transcript
            self.video_page.set_text(result.transcript.text)
            self.video_page.set_busy(False, t("video.done_text", name=result.audio_path.name))
            return
        self.video_page.set_text("")
        self.video_page.set_busy(False, t("video.done", name=result.audio_path.name))

    def _video_failed(self, message: str) -> None:
        self.video_page.set_busy(False, message)
        QMessageBox.warning(self, t("dialog.video"), message)

    def _copy(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text or "")

    def _save(self, text: str) -> None:
        path, _selected = QFileDialog.getSaveFileName(self, t("dialog.export"), "transcript.txt", transcript_export_filter())
        if not path:
            return
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix(".txt")
        try:
            segments = self.last_result.segments if self.last_result else []
            export_transcript(target, text or "", segments, self._current_settings())
        except Exception as exc:
            QMessageBox.warning(self, t("dialog.export"), str(exc))

    def _setup_tray(self) -> None:
        self.tray: QSystemTrayIcon | None = None
        self._tray_show: QAction | None = None
        self._tray_quit: QAction | None = None
        icon = app_icon()
        if icon.isNull() or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu(self)
        self._tray_show = QAction(self)
        self._tray_quit = QAction(self)
        self._tray_show.triggered.connect(self._show_from_tray)
        self._tray_quit.triggered.connect(self._quit_from_tray)
        menu.addAction(self._tray_show)
        menu.addSeparator()
        menu.addAction(self._tray_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self._retranslate_tray()
        self.tray.show()
        QApplication.instance().setQuitOnLastWindowClosed(False)

    def _retranslate_tray(self) -> None:
        if self.tray is None:
            return
        self.tray.setToolTip(t("tray.tooltip"))
        if self._tray_show is not None:
            self._tray_show.setText(t("tray.show"))
        if self._tray_quit is not None:
            self._tray_quit.setText(t("common.quit"))

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self) -> None:
        self._force_quit = True
        self.close()

    def _stop_workers(self) -> None:
        if self.live_worker and self.live_worker.isRunning():
            self.live_worker.request_stop()
            self.live_worker.wait(1500)
        if self.record_worker and self.record_worker.isRunning():
            self.record_worker.request_stop()
            self.record_worker.wait(1500)
        if self.file_worker and self.file_worker.isRunning():
            self.file_worker.wait(300)
        if self.video_worker and self.video_worker.isRunning():
            self.video_worker.wait(300)

    def closeEvent(self, event) -> None:
        if self.tray is not None and self.tray.isVisible() and not self._force_quit:
            event.ignore()
            self.hide()
            return
        self._stop_workers()
        if self.tray is not None:
            self.tray.hide()
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()
