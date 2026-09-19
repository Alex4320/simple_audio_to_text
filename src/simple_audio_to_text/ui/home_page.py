from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from simple_audio_to_text.assets import logo_pixmap
from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.ui.widgets import CARD_HEIGHT, GearButton, ModeCard, ModeStack


class HomePage(QWidget):
    open_file = Signal()
    open_live = Signal()
    open_record = Signal()
    open_video = Signal()
    open_settings = Signal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 36, 48, 36)
        root.setSpacing(28)

        top = QHBoxLayout()
        heading = QHBoxLayout()
        heading.setSpacing(16)
        self.logo = QLabel()
        self.logo.setFixedSize(72, 72)
        self._refresh_logo()
        brand = QVBoxLayout()
        brand.setSpacing(6)
        self.kicker = QLabel()
        self.kicker.setProperty("muted", True)
        self.kicker.setStyleSheet("font-size: 11px; letter-spacing: 1.4px;")
        self.title = QLabel()
        self.title.setProperty("hero", True)
        self.subtitle = QLabel()
        self.subtitle.setProperty("muted", True)
        brand.addWidget(self.kicker)
        brand.addWidget(self.title)
        brand.addWidget(self.subtitle)
        heading.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignTop)
        heading.addLayout(brand, 1)
        self.settings_btn = GearButton()
        self.settings_btn.clicked.connect(self.open_settings.emit)
        top.addLayout(heading, 1)
        top.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignTop)

        row = QWidget()
        row.setFixedHeight(CARD_HEIGHT)
        cards = QHBoxLayout(row)
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setSpacing(20)
        self.file_card = ModeCard("file", "", "")
        self.live_card = ModeCard("live", "", "")
        self.record_card = ModeCard("save", "", "", compact=True)
        self.video_card = ModeCard("video", "", "", compact=True)
        self.file_card.clicked.connect(self.open_file.emit)
        self.live_card.clicked.connect(self.open_live.emit)
        self.record_card.clicked.connect(self.open_record.emit)
        self.video_card.clicked.connect(self.open_video.emit)
        side = ModeStack(self.record_card, self.video_card)
        cards.addWidget(self.file_card, 1)
        cards.addWidget(self.live_card, 1)
        cards.addWidget(side, 1)

        self.footnote = QLabel()
        self.footnote.setProperty("muted", True)
        self.footnote.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root.addLayout(top)
        root.addStretch(1)
        root.addWidget(row)
        root.addStretch(1)
        root.addWidget(self.footnote)
        self.retranslate()

    def retranslate(self) -> None:
        self.kicker.setText(t("home.kicker"))
        self.title.setText(t("home.title"))
        self.subtitle.setText(t("home.subtitle"))
        self.file_card.set_texts(t("home.file_title"), t("home.file_sub"))
        self.live_card.set_texts(t("home.live_title"), t("home.live_sub"))
        self.record_card.set_texts(t("home.save_title"), t("home.save_sub"))
        self.video_card.set_texts(t("home.video_title"), t("home.video_sub"))
        self.footnote.setText(t("home.footnote"))
        self.settings_btn.retranslate()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_logo()

    def _refresh_logo(self) -> None:
        pixmap = logo_pixmap(72, self)
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap)
