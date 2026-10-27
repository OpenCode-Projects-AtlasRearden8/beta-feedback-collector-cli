"""Tests for per-chapter reports, reader summary, and backlog export."""

from betafeedback.backlog import build_backlog, write_backlog_csv, write_backlog_md
from betafeedback.cluster import cluster_items
from betafeedback.contradictions import find_contradictions
from betafeedback.normalize import collect_items
from betafeedback.readers import readers_summary
from betafeedback.report import chapter_report


def _fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"


def _all(tmp_path):
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    contradictions = find_contradictions(items)
    return items, clusters, contradictions


def test_chapter_report_structure(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    report = chapter_report(items, clusters, contradictions)
    assert report.startswith("# Revision To-Dos (per chapter)")
    for heading in ("## Chapter 1", "## Chapter 2", "## Chapter 3", "## Epilogue"):
        assert heading in report
    assert "### Plot-level flags (multiple readers)" in report
    assert "### Contradictions to resolve" in report
    assert "### Nitpicks" in report
    assert "Ana, Ben" in report  # consensus cluster shows its readers


def test_positive_comments_become_praise_not_nitpicks(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    report = chapter_report(items, clusters, contradictions)
    assert "### What readers loved (keep this)" in report
    assert "- [x] **" in report
    praise_section = report.split("### What readers loved")[1].split("###")[0]
    assert "Awesome voice for Maya" in praise_section
    assert "Loved the motel scene" in praise_section
    assert "Awesome voice" not in report.split("### Nitpicks")[0].split("### Plot-level")[1]


def test_readers_summary_structure(tmp_path):
    items, clusters, _ = _all(tmp_path)
    summary = readers_summary(items, clusters)
    assert summary.startswith("# Reader-by-Reader Summary")
    assert "| Ana |" in summary
    assert "| Ben |" in summary
    assert "| Cam |" in summary
    assert "## Details" in summary


def test_backlog_priority_order(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    rows = build_backlog(items, clusters, contradictions)
    priorities = [row[5] for row in rows]
    assert priorities == sorted(priorities)
    assert priorities[0] == 0  # consensus plot first
    assert rows[0][4].startswith("Fix (2 readers)")
    kinds = {row[2] for row in rows}
    assert kinds <= {"plot", "nitpick"}
    ids = [row[0] for row in rows]
    assert len(ids) == len(set(ids))


def test_backlog_markdown_and_csv_roundtrip(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    rows = build_backlog(items, clusters, contradictions)
    md_path = tmp_path / "revision-backlog.md"
    csv_path = tmp_path / "revision-backlog.csv"
    write_backlog_md(rows, md_path)
    write_backlog_csv(rows, csv_path)
    md = md_path.read_text(encoding="utf-8")
    assert md.startswith("# Revision Sprint 1 — Revision Backlog")
    assert f"| TSK-{len(rows):03d} |" in md
    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == "id,chapter,kind,raised_by,task,priority,state"
    assert len(lines) == len(rows) + 1


def test_backlog_skips_praise_and_contradiction_duplicates(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    rows = build_backlog(items, clusters, contradictions)
    tasks = " ".join(row[4] for row in rows)
    assert "Awesome voice" not in tasks
    assert "Loved the motel scene" not in tasks
    # the loved/hated ending cluster is a contradiction, not a duplicate fix row
    assert "Fix (2 readers): I loved the ending" not in tasks
    assert "Resolve contradiction" in tasks


def test_contradiction_page_numbering(tmp_path):
    items, clusters, contradictions = _all(tmp_path)
    report = chapter_report(items, clusters, contradictions)
    assert "Ch 3" in report or "Chapter 3" in report
