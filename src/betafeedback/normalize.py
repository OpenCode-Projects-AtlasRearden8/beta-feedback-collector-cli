"""Normalize reader feedback sheets (CSV or Markdown) into FeedbackItems."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .classify import classify
from .models import NITPICK, PLOT, FeedbackItem

CHAPTER_COL = ("chapter", "ch", "chapter number", "location", "section")
COMMENT_COL = ("comment", "comments", "note", "notes", "feedback", "observation", "issue")
READER_COL = ("reader", "reviewer", "name", "beta", "beta reader", "who")
ELEMENT_COL = ("element", "topic", "subject", "aspect", "area", "target", "scope", "focus")

_MD_CHAPTER_RE = re.compile(r"^#{1,6}\s*(?:chapter\s*)?(\S.*)$", re.IGNORECASE)
_MD_ELEMENT_RE = re.compile(r"^[-*+]\s*\(([^)\[]+)\)\s+(.*)$")
_MD_BULLET_RE = re.compile(r"^[-*+]\s+(.*)$")
_MD_BULLETED_KIND_RE = re.compile(r"^(nitpick|nit|plot|major|story|structure|minor)\b[\s:\-–—]*(.*)$", re.IGNORECASE)


def _clean(value) -> str:
    return (value or "").strip()


def _pick_column(fieldnames, candidates):
    lowered = {name.strip().lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def normalize_chapter(raw: str):
    """Normalize a chapter label; ints stay ints, text stays text."""
    raw = _clean(raw)
    match = re.search(r"(?:chapter|ch\s*\.?|#)\s*#?\s*(\d+)", raw, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.fullmatch(r"\d+", raw):
        return int(raw)
    return raw


def _normalize_kind_tag(value: str):
    value = _clean(value).lower()
    if value in ("nitpick", "nit", "minor", "line", "line-level", "prose", "small"):
        return NITPICK
    if value in ("plot", "major", "story", "structural", "structure", "big"):
        return PLOT
    return None


def load_csv_sheet(path: Path, default_reader: str) -> list:
    items = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return items
        chapter_col = _pick_column(reader.fieldnames, CHAPTER_COL)
        comment_col = _pick_column(reader.fieldnames, COMMENT_COL)
        reader_col = _pick_column(reader.fieldnames, READER_COL)
        element_col = _pick_column(reader.fieldnames, ELEMENT_COL)
        kind_col = _pick_column(
            reader.fieldnames,
            ("type", "kind", "severity", "level", "category", "comment type"),
        )
        if chapter_col is None or comment_col is None:
            raise ValueError(
                f"{path.name}: CSV needs at least 'chapter' and 'comment' columns; "
                f"found {list(reader.fieldnames)}"
            )
        for row in reader:
            text = _clean(row.get(comment_col, ""))
            if not text:
                continue
            chapter = normalize_chapter(row.get(chapter_col, ""))
            who = _clean(row.get(reader_col, "")) if reader_col else ""
            reader_name = who or default_reader
            element = _clean(row.get(element_col, "")) if element_col else ""
            hinted = _normalize_kind_tag(row.get(kind_col, "")) if kind_col else None
            items.append(
                FeedbackItem(
                    reader=reader_name,
                    chapter=chapter,
                    element=element or "General",
                    kind=classify(text, hinted),
                    text=text,
                    source_file=path.name,
                )
            )
    return items


def load_markdown_sheet(path: Path, default_reader: str) -> list:
    items = []
    chapter = "Unknown chapter"
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.rstrip()
            match = _MD_CHAPTER_RE.match(line)
            if match:
                chapter = normalize_chapter(match.group(1).strip())
                continue
            bullet = _MD_BULLET_RE.match(line)
            if not bullet:
                continue
            text = _clean(bullet.group(1))
            if not text:
                continue
            element = "General"
            element_match = _MD_ELEMENT_RE.match(line)
            if element_match:
                element = element_match.group(1).strip().title()
                text = _clean(element_match.group(2))
            hinted = None
            kind_match = _MD_BULLETED_KIND_RE.match(text)
            if kind_match:
                hinted = _normalize_kind_tag(kind_match.group(1))
                if hinted:
                    text = _clean(kind_match.group(2))
            if not text:
                continue
            items.append(
                FeedbackItem(
                    reader=default_reader,
                    chapter=chapter,
                    element=element if element not in (None, "") else "General",
                    kind=classify(text, hinted),
                    text=text,
                    source_file=path.name,
                )
            )
    return items


SHEET_SUFFIXES = {".csv": load_csv_sheet, ".md": load_markdown_sheet, ".markdown": load_markdown_sheet}


def load_sheet(path: Path, readers=None) -> list:
    """Load one feedback sheet; `readers` maps file stem -> reader name."""
    path = Path(path)
    loader = SHEET_SUFFIXES.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported sheet type: {path.name} (use .csv or .md)")
    stem = path.stem.lower()
    default_reader = (readers or {}).get(stem) or _detrivialize(path.stem)
    return loader(path, default_reader)


def _detrivialize(stem: str) -> str:
    cleaned = re.sub(r"[_-]+", " ", stem).strip()
    lower = cleaned.lower()
    if lower.startswith("reader "):
        cleaned = cleaned[len("reader "):]
    return cleaned.title() if cleaned else "Anonymous Reader"


def collect_items(folder, readers=None) -> list:
    """Collect and normalize every .csv/.md sheet in a folder."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Feedback folder not found: {folder}")
    items = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in SHEET_SUFFIXES:
            items.extend(load_sheet(path, readers))
    if not items:
        raise ValueError(f"No feedback sheets found in {folder} (need .csv or .md files)")
    return items


def write_normalized_csv(items, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["reader", "chapter", "element", "kind", "comment", "source"])
        for item in items:
            writer.writerow([item.reader, str(item.chapter), item.element, item.kind, item.text, item.source_file])


def write_normalized_json(items, path: Path) -> None:
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [item.to_dict() for item in items]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
