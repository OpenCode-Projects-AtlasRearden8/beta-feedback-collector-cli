"""Data model for normalized beta-reader feedback."""

from __future__ import annotations

from dataclasses import dataclass, field


NITPICK = "nitpick"
PLOT = "plot"
KINDS = (NITPICK, PLOT)


@dataclass
class FeedbackItem:
    reader: str
    chapter: str
    element: str
    kind: str
    text: str
    source_file: str = ""

    @property
    def chapter_key(self) -> str:
        if isinstance(self.chapter, int):
            return f"chapter_{self.chapter:03d}"
        return f"other_{self.chapter}"

    def to_dict(self) -> dict:
        return {
            "reader": self.reader,
            "chapter": str(self.chapter),
            "element": self.element,
            "kind": self.kind,
            "text": self.text,
            "source_file": self.source_file,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackItem":
        return cls(
            reader=data["reader"],
            chapter=_restore_chapter(data["chapter"]),
            element=data.get("element", "General"),
            kind=data.get("kind", NITPICK),
            text=data["text"],
            source_file=data.get("source_file", ""),
        )


def _restore_chapter(value: str):
    if value.startswith("chapter_"):
        try:
            return int(value[len("chapter_"):])
        except ValueError:
            pass
    if value.startswith("other_"):
        return value[len("other_"):]
    return value


@dataclass
class Cluster:
    chapter_key: str
    element: str
    kind: str
    items: list

    @property
    def readers(self) -> list:
        seen = []
        for item in self.items:
            if item.reader not in seen:
                seen.append(item.reader)
        return sorted(seen)

    @property
    def reader_count(self) -> int:
        return len(self.readers)

    @property
    def samples(self) -> list:
        seen = []
        for item in self.items:
            if item.text not in seen:
                seen.append(item.text)
        return seen

    def to_dict(self) -> dict:
        return {
            "chapter_key": self.chapter_key,
            "element": self.element,
            "kind": self.kind,
            "readers": self.readers,
            "items": [item.to_dict() for item in self.items],
        }
