"""Tests for sheet normalization (CSV + Markdown)."""

import pytest

from betafeedback.normalize import collect_items, load_sheet, normalize_chapter
from betafeedback.models import NITPICK, PLOT

FIXTURES = None


def _fixtures_dir():
    from pathlib import Path

    return Path(__file__).parent / "fixtures"


def test_normalize_chapter_variants():
    assert normalize_chapter("Chapter 5") == 5
    assert normalize_chapter("ch. 12") == 12
    assert normalize_chapter("3") == 3
    assert normalize_chapter("Epilogue") == "Epilogue"


def test_collect_items_counts():
    items = collect_items(_fixtures_dir())
    readers = {item.reader for item in items}
    assert readers == {"Ana", "Ben", "Cam"}
    assert len(items) >= 12
    assert all(item.text for item in items)


def test_reader_inferred_from_mapping():
    items = collect_items(_fixtures_dir(), readers={"reader_ana": "Ana P.", "reader_ben": "Ben T.", "reader_cam": "Cam"})
    assert any(item.reader == "Ana P." for item in items)


def test_csv_explicit_kind_column_respected():
    items = load_sheet(_fixtures_dir() / "reader_cam.csv", {})
    by_text = {item.text: item for item in items}
    magic = next(v for k, v in by_text.items() if "magic system" in k)
    grammar = next(v for k, v in by_text.items() if "comma splice" in k)
    assert magic.kind == PLOT
    assert grammar.kind == NITPICK
    assert magic.element == "Magic"
    assert grammar.element == "Sentences"


def test_markdown_bullets_elements_and_tags():
    items = load_sheet(_fixtures_dir() / "reader_ben.md", {})
    pacing = next(i for i in items if "drags" in i.text)
    assert pacing.kind == PLOT
    assert pacing.element == "Pacing"
    prose = next(i for i in items if "motel scene" in i.text)
    assert prose.kind == NITPICK  # keyword heuristic: "vivid" is not a plot word


def test_markdown_epilogue_is_non_numeric_chapter():
    items = load_sheet(_fixtures_dir() / "reader_ben.md", {})
    epilogue = [i for i in items if i.chapter == "Epilogue"]
    assert epilogue
    assert all(i.kind == NITPICK for i in epilogue)


def test_singular_type_column_mapping():
    items = load_sheet(_fixtures_dir() / "reader_cam.csv", {})
    assert any(i.kind == PLOT for i in items)
    assert any(i.kind == NITPICK for i in items)


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        load_sheet(_fixtures_dir() / "nope.txt", {})


def test_missing_folder_raises():
    with pytest.raises(FileNotFoundError):
        collect_items(_fixtures_dir() / "does-not-exist")
