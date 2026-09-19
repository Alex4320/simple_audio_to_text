from __future__ import annotations

import html
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from simple_audio_to_text.services.i18n import t
from simple_audio_to_text.services.postprocess import Segment, remove_fillers
from simple_audio_to_text.services.settings import AppSettings

EXPORT_FILTER = (
    "Текст (*.txt);;"
    "Субтитры SubRip (*.srt);;"
    "WebVTT (*.vtt);;"
    "JSON (*.json);;"
    "Markdown (*.md);;"
    "Word (*.docx)"
)


def _clean(text: str, settings: AppSettings) -> str:
    value = text.strip()
    if settings.remove_fillers:
        value = remove_fillers(value)
    return value


def _clock(seconds: float, comma: bool) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    sep = "," if comma else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"


def _usable_segments(segments: list[Segment], settings: AppSettings) -> list[Segment]:
    ready: list[Segment] = []
    for item in segments:
        text = _clean(item.text, settings)
        if text:
            ready.append(Segment(item.start, item.end, text, item.speaker))
    return ready


def _plain(text: str, segments: list[Segment], settings: AppSettings) -> str:
    ready = _usable_segments(segments, settings)
    if ready:
        from simple_audio_to_text.services.postprocess import format_transcript

        return format_transcript(ready, settings)
    return _clean(text, settings)


def _srt(segments: list[Segment], text: str, settings: AppSettings) -> str:
    ready = _usable_segments(segments, settings)
    if not ready and text.strip():
        ready = [Segment(0, max(2.0, len(text.split()) * 0.4), _clean(text, settings))]
    lines: list[str] = []
    for index, item in enumerate(ready, start=1):
        end = item.end if item.end > item.start else item.start + 1.5
        speaker = f"{t('export.speaker', n=item.speaker)}: " if settings.split_speakers and item.speaker else ""
        lines.extend(
            [
                str(index),
                f"{_clock(item.start, True)} --> {_clock(end, True)}",
                f"{speaker}{item.text}",
                "",
            ]
        )
    return "\n".join(lines).strip() + ("\n" if lines else "")


def _vtt(segments: list[Segment], text: str, settings: AppSettings) -> str:
    body = _srt(segments, text, settings).replace(",", ".")
    if not body.strip():
        return "WEBVTT\n"
    numbered: list[str] = []
    for block in body.strip().split("\n\n"):
        rows = block.split("\n")
        numbered.append("\n".join(rows[1:] if rows and rows[0].isdigit() else rows))
    return "WEBVTT\n\n" + "\n\n".join(numbered) + "\n"


def _markdown(segments: list[Segment], text: str, settings: AppSettings) -> str:
    ready = _usable_segments(segments, settings)
    if not ready:
        return f"# {t('export.heading')}\n\n" + _clean(text, settings) + "\n"
    lines = [f"# {t('export.heading')}", ""]
    for item in ready:
        stamp = _clock(item.start, False)[:8]
        who = f"{t('export.speaker', n=item.speaker)} · " if settings.split_speakers and item.speaker else ""
        lines.append(f"- **{stamp}** {who}{item.text}")
    return "\n".join(lines) + "\n"


def _json(segments: list[Segment], text: str, settings: AppSettings) -> str:
    ready = _usable_segments(segments, settings)
    payload = {
        "text": _plain(text, segments, settings),
        "segments": [
            {
                "start": round(item.start, 3),
                "end": round(item.end, 3),
                "text": item.text,
                "speaker": item.speaker,
            }
            for item in ready
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _docx_xml(text: str) -> str:
    paragraphs = text.splitlines() or [""]
    body = []
    for line in paragraphs:
        body.append(
            "<w:p><w:r><w:t xml:space=\"preserve\">"
            + html.escape(line)
            + "</w:t></w:r></w:p>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + "".join(body)
        + "</w:body></w:document>"
    )


def _write_docx(path: Path, text: str) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", _docx_xml(text))


def export_transcript(
    path: Path | str,
    text: str,
    segments: list[Segment] | None,
    settings: AppSettings,
) -> None:
    target = Path(path)
    suffix = target.suffix.lower()
    bits = segments or []
    if suffix == ".srt":
        target.write_text(_srt(bits, text, settings), encoding="utf-8")
        return
    if suffix == ".vtt":
        target.write_text(_vtt(bits, text, settings), encoding="utf-8")
        return
    if suffix == ".json":
        target.write_text(_json(bits, text, settings), encoding="utf-8")
        return
    if suffix == ".md":
        target.write_text(_markdown(bits, text, settings), encoding="utf-8")
        return
    if suffix == ".docx":
        _write_docx(target, _plain(text, bits, settings))
        return
    target.write_text(_plain(text, bits, settings), encoding="utf-8")
