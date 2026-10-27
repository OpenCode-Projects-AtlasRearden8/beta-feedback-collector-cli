"""End-to-end CLI tests via the console entry point."""

import json

import pytest

from betafeedback.cli import main


def _fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"


def test_run_pipeline_writes_all_outputs(tmp_path, capsys):
    out = tmp_path / "out"
    code = main(["run", "--folder", str(_fixtures_dir()), "--out", str(out)])
    assert code == 0
    expected = [
        "normalized-feedback.csv",
        "normalized-feedback.json",
        "chapter-report.md",
        "readers-summary.md",
        "revision-backlog.md",
        "revision-backlog.csv",
    ]
    for name in expected:
        assert (out / name).is_file()
    payload = json.loads((out / "normalized-feedback.json").read_text(encoding="utf-8"))
    assert len(payload) >= 12
    assert {"reader", "chapter", "element", "kind", "text"} <= set(payload[0])
    printed = capsys.readouterr().out
    assert "Wrote 6 files" in printed


def test_collect_single_command(tmp_path):
    out = tmp_path / "norm"
    code = main(["collect", "--folder", str(_fixtures_dir()), "--out", str(out)])
    assert code == 0
    assert (out / "normalized-feedback.csv").is_file()
    csv_text = (out / "normalized-feedback.csv").read_text(encoding="utf-8")
    assert csv_text.startswith("reader,chapter,element,kind,comment,source")
    assert "Ana" in csv_text


def test_report_and_summary_and_contradictions_commands(tmp_path):
    out = tmp_path / "reports"
    for command, filename in (
        ("report", "chapter-report.md"),
        ("summary", "readers-summary.md"),
        ("contradictions", "contradictions.md"),
    ):
        code = main([command, "--folder", str(_fixtures_dir()), "--out", str(out)])
        assert code == 0
        assert (out / filename).is_file()
    contradictions = (out / "contradictions.md").read_text(encoding="utf-8")
    assert "Ana" in contradictions and "Ben" in contradictions


def test_bad_folder_exits_nonzero():
    with pytest.raises(FileNotFoundError):
        main(["run", "--folder", str(_fixtures_dir() / "missing"), "--out", "/tmp/never"])


def test_synthetic_contradiction_scenario(tmp_path):
    folder = tmp_path / "feedback"
    folder.mkdir()
    (folder / "r1.csv").write_text(
        "Chapter,Comment\n2,I loved the duel it was great\n", encoding="utf-8"
    )
    (folder / "r2.csv").write_text(
        "Chapter,Comment\n2,I hated the duel it was boring\n", encoding="utf-8"
    )
    out = tmp_path / "out"
    code = main(["contradictions", "--folder", str(folder), "--out", str(out)])
    assert code == 0
    text = (out / "contradictions.md").read_text(encoding="utf-8")
    assert "R1" in text and "R2" in text
    assert "loved" in text and "hated" in text
