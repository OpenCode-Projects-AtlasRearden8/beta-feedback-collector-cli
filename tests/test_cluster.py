"""Tests for clustering recurring comments by chapter."""

from betafeedback.cluster import cluster_items
from betafeedback.normalize import collect_items


def _fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"


def test_slow_opening_clusters_across_readers():
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    slow = [c for c in clusters if "too slow" in c.samples[0].lower()]
    assert len(slow) == 1
    cluster = slow[0]
    assert cluster.reader_count == 2
    assert set(cluster.readers) == {"Ana", "Ben"}
    assert len(cluster.items) == 2


def test_typo_clusters_within_reader_pairs():
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    typo = [c for c in clusters if c.samples[0].lower().startswith("typo")]
    assert len(typo) == 1
    assert typo[0].reader_count == 2


def test_villain_backstory_is_one_consensus_cluster():
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    backstory = [c for c in clusters if "backstory" in c.samples[0].lower() or "backstory" in " ".join(c.samples).lower()]
    assert len(backstory) == 1
    cluster = backstory[0]
    assert cluster.reader_count == 2
    assert cluster.kind == "plot"


def test_chapters_stay_separate():
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    chapters = {c.chapter_key for c in clusters}
    assert "chapter_001" in chapters
    assert "chapter_003" in chapters
    assert any(k.startswith("other_") for k in chapters)


def test_clusters_all_have_items():
    items = collect_items(_fixtures_dir())
    clusters = cluster_items(items)
    assert all(c.items for c in clusters)
    total = sum(len(c.items) for c in clusters)
    assert total == len(items)
