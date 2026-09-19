from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

BG = "#100f0d"
SURFACE = "#1b1915"
SURFACE_2 = "#24221c"
LINE = "#3c362c"
TEXT = "#f4efe6"
MUTED = "#9b9386"
ACCENT = "#e89a33"
ACCENT_HOVER = "#f2b056"
DANGER = "#c45c4a"


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    font = QFont()
    font.setFamilies(["Segoe UI", "Ubuntu", "Noto Sans", "DejaVu Sans"])
    font.setPointSize(10)
    app.setFont(font)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SURFACE_2))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE_2))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
    app.setPalette(palette)
    app.setStyleSheet(STYLES)


STYLES = f"""
QMainWindow, QWidget#root {{
    background: {BG};
    color: {TEXT};
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QLabel[muted="true"] {{
    color: {MUTED};
}}
QLabel[hero="true"] {{
    font-size: 34px;
    font-weight: 650;
    letter-spacing: -0.4px;
}}
QLabel[pageTitle="true"] {{
    font-size: 22px;
    font-weight: 620;
}}
QLabel[cardTitle="true"] {{
    font-size: 20px;
    font-weight: 620;
}}
QLabel[cardTitleMini="true"] {{
    font-size: 16px;
    font-weight: 620;
}}
QPushButton {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {LINE};
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 13px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
}}
QPushButton:disabled {{
    color: {MUTED};
    border-color: {LINE};
}}
QPushButton[primary="true"] {{
    background: {ACCENT};
    color: {BG};
    border: none;
    font-weight: 620;
}}
QPushButton[primary="true"]:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton[danger="true"] {{
    background: {DANGER};
    color: {TEXT};
    border: none;
}}
QPushButton[iconish="true"] {{
    min-width: 42px;
    max-width: 42px;
    min-height: 42px;
    max-height: 42px;
    border-radius: 21px;
    padding: 0;
    font-size: 16px;
}}
QFrame#card, QFrame#drop, QFrame#panel {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 18px;
}}
QFrame#drop {{
    border-style: dashed;
    border-width: 1px;
}}
QFrame#modeCard, QFrame#modeStack {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 22px;
}}
QFrame#modeCard:hover, QFrame#modeStack:hover {{
    border-color: {ACCENT};
}}
QFrame#modeCard:hover {{
    background: {SURFACE_2};
}}
QFrame#modeCardMini {{
    background: transparent;
    border: none;
    border-radius: 21px;
}}
QFrame#modeCardMini:hover {{
    background: {SURFACE_2};
}}
QFrame#modeSplit {{
    background: {LINE};
    border: none;
    margin: 0 16px;
}}
QCheckBox {{
    color: {TEXT};
    spacing: 10px;
    font-size: 14px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {LINE};
    background: {SURFACE_2};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QTextEdit {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {LINE};
    border-radius: 16px;
    padding: 14px;
    font-size: 14px;
    selection-background-color: {ACCENT};
    selection-color: {BG};
}}
QListWidget {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {LINE};
    border-radius: 16px;
    padding: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 12px;
    border-radius: 10px;
    margin: 2px;
}}
QListWidget::item:selected {{
    background: {ACCENT};
    color: {BG};
}}
QListWidget::item:hover {{
    background: {SURFACE_2};
}}
QComboBox {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {LINE};
    border-radius: 10px;
    padding: 8px 12px;
    min-width: 160px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: {BG};
    border: 1px solid {LINE};
}}
QProgressBar {{
    background: {SURFACE_2};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 6px;
}}
QFrame#loadStatus {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 12px;
}}
QProgressBar#loadBar {{
    min-height: 16px;
    height: 16px;
    color: {TEXT};
    font-size: 11px;
    font-weight: 600;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px;
}}
QScrollBar::handle:vertical {{
    background: {LINE};
    border-radius: 4px;
    min-height: 32px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QLabel#recBanner {{
    background: {DANGER};
    color: {TEXT};
    border-radius: 12px;
    padding: 10px 14px;
    font-weight: 700;
    font-size: 14px;
}}
"""
