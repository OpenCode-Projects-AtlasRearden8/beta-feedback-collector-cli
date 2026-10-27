"""Command-line interface for beta-feedback-collector-cli."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .backlog import build_backlog, write_backlog_csv, write_backlog_md
from .brainstorm import DEFAULT_BASE_URL, DEFAULT_MODEL, BrainstormError, brainstorm_themes
from .cluster import cluster_items
from .contradictions import find_contradictions
from .models import FeedbackItem
from .normalize import collect_items, write_normalized_csv, write_normalized_json
from .readers import readers_summary
from .report import chapter_report

OUT_DIR = "beta-feedback-out"


def _do_pipeline(args) -> list:
    items = collect_items(args.folder, readers=_parse_readers(args.readers))
    clusters = cluster_items(items)
    contradictions = find_contradictions(items)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_normalized_csv(items, out / "normalized-feedback.csv")
    write_normalized_json(items, out / "normalized-feedback.json")
    (out / "chapter-report.md").write_text(chapter_report(items, clusters, contradictions), encoding="utf-8")
    (out / "readers-summary.md").write_text(readers_summary(items, clusters), encoding="utf-8")
    rows = build_backlog(items, clusters, contradictions)
    write_backlog_md(rows, out / "revision-backlog.md", sprint_name=args.sprint)
    write_backlog_csv(rows, out / "revision-backlog.csv")
    print(f"Wrote 6 files to {out}/ from {len(items)} comments by "
          f"{len({i.reader for i in items})} readers across "
          f"{len({i.chapter_key for i in items})} chapters.")
    return items


def _parse_readers(spec) -> dict:
    mapping = {}
    if not spec:
        return mapping
    for pair in spec.split(","):
        if "=" in pair:
            stem, name = pair.split("=", 1)
            mapping[stem.strip().lower()] = name.strip()
    return mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="beta-reader",
        description="Normalize beta-reader feedback sheets (CSV/Markdown), cluster "
        "recurring comments by chapter, and generate revision reports.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--folder", default="feedback", help="Folder containing .csv/.md feedback sheets (default: feedback)")
    common.add_argument("--out", default=OUT_DIR, help="Output directory (default: beta-feedback-out)")
    common.add_argument("--readers", default="", help='Optional reader names, e.g. "reader_ana=Ana,reader_ben=Ben"')
    common.add_argument("--sprint", default="Revision Sprint 1", help="Sprint name for the backlog header")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", parents=[common], help="Full pipeline: normalize, cluster, report, summary, backlog")
    sub.add_parser("collect", parents=[common], help="Normalize sheets into one CSV/JSON feed")
    sub.add_parser("report", parents=[common], help="Per-chapter revision to-do report")
    sub.add_parser("summary", parents=[common], help="Reader-by-reader summary")
    sub.add_parser("contradictions", parents=[common], help="Highlight contradictory comments between readers")

    brainstorm = sub.add_parser("brainstorm", parents=[common], help="Optional theme brainstorm via local LLM (Ollama default)")
    brainstorm.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible endpoint (default: %(default)s)")
    brainstorm.add_argument("--model", default=DEFAULT_MODEL, help="Model name (default: %(default)s)")
    brainstorm.add_argument("--timeout", type=int, default=30)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        args.command = "run"
    if args.command == "run":
        _do_pipeline(args)
        return 0
    if args.command == "brainstorm":
        return brainstorm_cli(args)

    items = collect_items(args.folder, readers=_parse_readers(args.readers))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.command == "collect":
        write_normalized_csv(items, out / "normalized-feedback.csv")
        write_normalized_json(items, out / "normalized-feedback.json")
        print(f"Normalized {len(items)} comments -> {out}/normalized-feedback.csv")
        return 0
    clusters = cluster_items(items)
    contradictions = find_contradictions(items)
    targets = {
        "report": ("chapter-report.md", lambda: chapter_report(items, clusters, contradictions)),
        "summary": ("readers-summary.md", lambda: readers_summary(items, clusters)),
        "contradictions": ("contradictions.md", lambda: _contradictions_md(contradictions)),
    }
    filename, builder = targets[args.command]
    (out / filename).write_text(builder(), encoding="utf-8")
    print(f"Wrote {out / filename}")
    return 0


def _contradictions_md(contradictions) -> str:
    lines = ["# Contradictions Between Readers", ""]
    if not contradictions:
        lines.append("None found. (Either the manuscript is consistent, or the readers were too polite.)")
        return "\n".join(lines) + "\n"
    for ra, ta, rb, tb, chapter_key in contradictions:
        chapter = f"Ch {int(chapter_key[len('chapter_'):])}" if chapter_key.startswith("chapter_") else chapter_key
        lines.append(f"- **{chapter}:** {ra} says “{ta}”; {rb} says “{tb}”")
    return "\n".join(lines) + "\n"


def brainstorm_cli(args, extra=None) -> int:  # kept for direct invocation in tests
    items = collect_items(args.folder)
    try:
        text = brainstorm_themes(items, base_url=args.base_url, model=args.model, timeout=args.timeout)
    except BrainstormError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
