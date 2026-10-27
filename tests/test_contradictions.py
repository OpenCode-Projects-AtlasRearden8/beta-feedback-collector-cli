"""Tests for contradiction detection between readers."""

from betafeedback.contradictions import find_contradictions
from betafeedback.normalize import collect_items


def _fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"


def test_love_hate_ending_contradiction_detected():
    items = collect_items(_fixtures_dir())
    found = find_contradictions(items)
    targets = [c for c in found if c[4] == "chapter_003"]
    assert len(targets) == 1
    ra, ta, rb, tb, _ = targets[0]
    readers = {ra, rb}
    assert readers <= {"Ana", "Ben"}
    assert any("loved" in text.lower() for text in (ta, tb))
    assert any("hated" in text.lower() for text in (ta, tb))


def test_backstory_more_less_contradiction_detected():
    items = collect_items(_fixtures_dir())
    found = find_contradictions(items)
    targets = [c for c in found if c[4] == "chapter_002"]
    assert len(targets) == 1
    texts = (targets[0][1], targets[0][3])
    assert any("more" in text.lower() for text in texts)
    assert any("less" in text.lower() for text in texts)


def test_no_contradictions_within_single_reader():
    items = [i for i in collect_items(_fixtures_dir()) if i.reader == "Cam"]
    assert find_contradictions(items) == []


def test_no_duplicates_in_output():
    items = collect_items(_fixtures_dir())
    found = find_contradictions(items)
    keys = [(min(a[1], a[3]), max(a[1], a[3])) for a in found]
    assert len(keys) == len(set(keys))
