"""Revision sprint backlog export (Markdown + CSV).

Priority: consensus plot flags first (P0), then contradictions (P1),
then single-reader plot flags (P2), then nitpicks (P3).
"""

from __future__ import annotations

import csv
from pathlib import Path

from .contradictions import sentiment
from .models import NITPICK, PLOT


def _chapter_number(chapter_key: str) -> str:
    if chapter_key.startswith("chapter_"):
        return str(int(chapter_key[len("chapter_"):]))
    if chapter_key.startswith("other_"):
        return chapter_key[len("other_"):]
    return chapter_key


def build_backlog(items, clusters, contradictions) -> list:
    """Return rows: [id, chapter, kind, raised_by, task, priority, state]."""
    rows = []

    def make_row(chapter_key, kind, raised_by, task, priority):
        rows.append(
            [
                f"TSK-{len(rows) + 1:03d}",
                _chapter_number(chapter_key),
                kind,
                raised_by,
                task,
                priority,
                "Ready",
            ]
        )

    contradiction_texts = set()
    for _, ta, _, tb, _ in contradictions:
        contradiction_texts.add(ta)
        contradiction_texts.add(tb)
    contested_texts = {(min(ta, tb), max(ta, tb)) for _, ta, _, tb, _ in contradictions}

    consensus, singles, nitpicks = [], [], []
    for cluster in clusters:
        texts = {item.text for item in cluster.items}
        # skip pure praise
        if not (texts & contradiction_texts) and all(sentiment(t) == 1 for t in texts):
            continue
        # skip clusters whose items already form a contradiction pair
        if any(ta in texts and tb in texts for ta, tb in contested_texts):
            continue
        task = f"Fix ({cluster.reader_count} reader{'s' if cluster.reader_count > 1 else ''}): {cluster.samples[0]}"
        bucket = nitpicks if cluster.kind == NITPICK else (consensus if cluster.reader_count > 1 else singles)
        bucket.append((cluster.chapter_key, cluster.kind, ", ".join(cluster.readers), task))

    for ra, ta, rb, tb, chapter_key in contradictions:
        task = f"Resolve contradiction: “{ta}” ({ra}) vs “{tb}” ({rb})"
        singles.append((chapter_key, PLOT, f"{ra} vs {rb}", task))

    plot_flags = [  # single-reader plot flags that are not contradiction tasks
        row for row in singles if not row[3].startswith("Resolve contradiction:")
    ]
    resolved = [row for row in singles if row[3].startswith("Resolve contradiction:")]

    for chapter_key, kind, raised_by, task in consensus:
        make_row(chapter_key, kind, raised_by, task, 0)
    for chapter_key, kind, raised_by, task in resolved:
        make_row(chapter_key, kind, raised_by, task, 1)
    for chapter_key, kind, raised_by, task in plot_flags:
        make_row(chapter_key, kind, raised_by, task, 2)
    for chapter_key, kind, raised_by, task in nitpicks:
        make_row(chapter_key, kind, raised_by, task, 3)
    return rows


def write_backlog_md(rows, path, sprint_name="Revision Sprint 1") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {sprint_name} — Revision Backlog",
        "",
        "| ID | Chapter | Kind | Raised by | Task | Priority | State |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, chapter, kind, raised, task, priority, state in rows:
        lines.append(f"| {key} | {chapter} | {kind} | {raised} | {task} | P{priority} | {state} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_backlog_csv(rows, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "chapter", "kind", "raised_by", "task", "priority", "state"])
        for key, chapter, kind, raised, task, priority, state in rows:
            writer.writerow([key, chapter, kind, raised, task, f"P{priority}", state])
