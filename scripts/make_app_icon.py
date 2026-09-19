from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication

BG = QColor("#14120f")
ACCENT = QColor("#e89a33")
CREAM = QColor("#f4efe6")
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256, 512, 1024)


def _draw_logo(painter: QPainter, size: int) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, size >= 24)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.fillRect(0, 0, size, size, Qt.GlobalColor.transparent)

    pad = max(1.0, size * 0.02)
    tile = QRectF(pad, pad, size - pad * 2, size - pad * 2)
    radius = size * (0.22 if size >= 32 else 0.18)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(BG)
    painter.drawRoundedRect(tile, radius, radius)

    unit = size / 256.0
    painter.translate(size / 2, size / 2)
    painter.scale(unit, unit)
    painter.translate(-128, -128)

    gold = ACCENT
    light = CREAM if size >= 40 else ACCENT
    stroke = 18 if size <= 24 else 14 if size <= 32 else 13
    painter.setBrush(Qt.BrushStyle.NoBrush)
    pen = QPen(gold)
    pen.setWidthF(stroke)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    if size <= 24:
        capsule = QPainterPath()
        capsule.addRoundedRect(QRectF(92, 52, 72, 108), 36, 36)
        painter.fillPath(capsule, gold)
        painter.drawLine(QPointF(128, 168), QPointF(128, 198))
        painter.drawLine(QPointF(96, 200), QPointF(160, 200))
        return

    capsule = QPainterPath()
    capsule.addRoundedRect(QRectF(70, 46, 60, 100), 30, 30)
    painter.fillPath(capsule, light)
    painter.drawPath(capsule)
    painter.drawArc(QRectF(56, 78, 88, 94), 200 * 16, 140 * 16)
    painter.drawLine(QPointF(100, 172), QPointF(100, 198))
    painter.drawLine(QPointF(72, 200), QPointF(128, 200))
    painter.drawLine(QPointF(186, 86), QPointF(226, 86))
    painter.drawLine(QPointF(186, 118), QPointF(236, 118))
    painter.drawLine(QPointF(186, 150), QPointF(218, 150))
    if size >= 48:
        painter.drawArc(QRectF(132, 84, 44, 72), -70 * 16, 140 * 16)


def render_logo(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    _draw_logo(painter, size)
    painter.end()
    return image


def _bmp_icon_image(image: QImage) -> bytes:
    size = image.width()
    and_row = ((size + 31) // 32) * 4
    header = bytearray(40)
    header[0:4] = (40).to_bytes(4, "little")
    header[4:8] = size.to_bytes(4, "little")
    header[8:12] = (size * 2).to_bytes(4, "little")
    header[12:14] = (1).to_bytes(2, "little")
    header[14:16] = (32).to_bytes(2, "little")
    pixels = bytearray()
    mask = bytearray()
    for y in range(size - 1, -1, -1):
        and_bits = 0
        bit = 7
        and_row_bytes = bytearray(and_row)
        and_index = 0
        for x in range(size):
            color = image.pixelColor(x, y)
            pixels += bytes((color.blue(), color.green(), color.red(), color.alpha()))
            if color.alpha() < 128:
                and_row_bytes[and_index] |= 1 << bit
            bit -= 1
            if bit < 0:
                bit = 7
                and_index += 1
        mask += and_row_bytes
    return bytes(header) + bytes(pixels) + bytes(mask)


def write_ico(frames: list[tuple[int, QImage]], dest: Path) -> None:
    payloads = [(size, _bmp_icon_image(image)) for size, image in frames if size <= 256]
    header = bytearray()
    header += (0).to_bytes(2, "little")
    header += (1).to_bytes(2, "little")
    header += len(payloads).to_bytes(2, "little")
    offset = 6 + 16 * len(payloads)
    body = bytearray()
    for size, data in payloads:
        width = 0 if size >= 256 else size
        header += bytes((width, width, 0, 0))
        header += (1).to_bytes(2, "little")
        header += (32).to_bytes(2, "little")
        header += len(data).to_bytes(4, "little")
        header += offset.to_bytes(4, "little")
        body += data
        offset += len(data)
    dest.write_bytes(bytes(header) + bytes(body))


def main() -> None:
    QApplication([])
    root = Path(__file__).resolve().parents[1]
    packaged = root / "src" / "simple_audio_to_text" / "assets"
    public = root / "assets"
    packaged.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    rendered: dict[int, QImage] = {}
    for size in ICON_SIZES:
        image = render_logo(size)
        rendered[size] = image
        name = "logo.png" if size == 1024 else f"logo-{size}.png"
        image.save(str(packaged / name), "PNG")
        if size in {256, 1024}:
            image.save(str(public / name), "PNG")

    ico_frames = [(size, rendered[size]) for size in (16, 20, 24, 32, 48, 64, 128, 256)]
    write_ico(ico_frames, packaged / "app.ico")
    (public / "app.ico").write_bytes((packaged / "app.ico").read_bytes())
    (public / "logo.png").write_bytes((packaged / "logo.png").read_bytes())
    print(f"Wrote {packaged / 'app.ico'} ({(packaged / 'app.ico').stat().st_size} bytes)")


if __name__ == "__main__":
    main()
