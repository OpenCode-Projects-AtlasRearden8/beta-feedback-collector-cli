"""Reader-by-reader summary (Markdown)."""

from __future__ import annotations

import re

_TAG_PREFIX_RE = re.compile(
    r"^\s*[\[\(]?\s*(nitpick|nit|plot|major|minor|story|structure)\b[\]\):]\s*",
    re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    return _TAG_PREFIX_RE.sub("", text).strip()


def _chapter_title(chapter_key: str) -> str:
    if chapter_key.startswith("chapter_"):
        return f"Ch {int(chapter_key[len('chapter_'):])}"
    return chapter_key[len("other_"):] if chapter_key.startswith("other_") else chapter_key


def readers_summary(items, clusters) -> str:
    lines = ["# Reader-by-Reader Summary", "", "| Reader | Comments | Chapters flagged | Plot flags | Top nits |", "|---|---|---|---|---|"]
    readers = sorted({item.reader for item in items})
    for reader in readers:
        mine = [item for item in items if item.reader == reader]
        plot_flags = [item for item in mine if item.kind == "plot"]
        nits = [item for item in mine if item.kind == "nitpick"]
        chapters = ", ".join(sorted({_chapter_title(i.chapter_key) for i in mine}))
        top_nits = "; ".join(_clean_text(item.text) for item in nits[:2]) or "—"
        lines.append(
            f"| {reader} | {len(mine)} | {chapters or '—'} | {len(plot_flags)} | {top_nits} |"
        )
    lines.append("")

    lines.append("## Details")
    lines.append("")
    for reader in readers:
        mine = [item for item in items if item.reader == reader]
        lines.append(f"### {reader}")
        lines.append("")
        plot_flags = [item for item in mine if item.kind == "plot"]
        if plot_flags:
            lines.append("**Plot-level flags:**")
            for flag in plot_flags:
                lines.append(f"- {_chapter_title(flag.chapter_key)}: {_clean_text(flag.text)}")
            lines.append("")
        nits = [item for item in mine if item.kind == "nitpick"]
        if nits:
            lines.append(f"**Nitpicks ({len(nits)}):**")
            for nit in nits[:5]:
                lines.append(f"- {_chapter_title(nit.chapter_key)}: {_clean_text(nit.text)}")
            if len(nits) > 5:
                lines.append(f"- …and {len(nits) - 5} more")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
